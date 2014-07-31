#!/usr/bin/env pypy
# vim: set fileencoding=utf8:
'''
Rhodes, a tool for monitoring and tracking which devices are using your 
bandwidth. Designed for use with Linux-based routers (i.e. devices which act as 
the gateway between internal LAN and external WAN). 

So-called after the island in Greece, which was an important maritime port 
in ancient times which tracked the comings and goings of vessels for the 
purposes of taxation.

:Variables:
    grDBPath : str
        File-system path to directory where Round-Robin Database files (*.rrd) 
        are to be stored, one per device.
    grRRDCacheDaemon : str
        File-system path to Unix socket on which the Round Robin Database Cache 
        Daemon is listening for update. This process buffers updates to reduce 
        disk I/O.
    grInterface : str
        String identifier for the network interface to monitor, e.g. ``eth0``
    grDeviceNames : str
        File-system path to a plain-text file which contains human readable 
        names for MAC addresses. Format: One entry per line consisting of a 
        lower-case hexadecimal MAC address string (no grouping characters, such 
        as colons and dashes), followed by whitespace, followed by the 
        human-readable name. E.g.::

            0004edbf98c0    home.gateway (Billion Electric Co.)
            0017fa731906    Xbox360
            745e1c56c297    Pioneer SX-LX57
            7831c1be0c34    Az Pro (Macbook Pro)
            80ea96e6214e    Roberts-AirPort-Time-Capsule
'''

import os
import collections

# =============================================================================
# CONFIGURATION
# =============================================================================
grDBPath = os.path.join( os.path.dirname( __file__ ) )
grRRDCacheDaemon = os.path.join( grDBPath, 'rrdcached.sock' )
grInterface = 'eth0'
grDeviceNames = '~pi/MAC.txt'

assert os.path.exists(grRRDCacheDaemon), "Please start: rrdcached -l unix:./rrdcached.sock -p rrdcached.pid"

# =============================================================================
# TYPES
# =============================================================================

# Data that is persisted to our databases
Sample = collections.namedtuple('Sample', ['iTime', 'iOctetsRX', 'iOctetsTX'])

# Output from TCPdump which we digest and batch into samples of 1-second
Record = collections.namedtuple('Record',
        ['iTime', 'iMACSource', 'iMACDestination', 'iLength'])

# =============================================================================
class Device( object ):
    '''
    Represents a device directly connected to the network. A typical network 
    has multiple end-user devices, and a single accessible WAN gateway (e.g. 
    Internet Service Provider's nearest hop).

    Records and persists coarse usage data: octets in, and octets out. No 
    filtering is performed, as it is assumed the Linux gateway (from which this 
    script obtains its data) is configured such that it does *not* forward 
    LAN-to-LAN data.

    :IVariables:
        rID : str
            Device identifier used to determine the filename of the resulting 
            *.rrd file.  Conventionally, this is the lower-case hexadecimal 
            representation of the device's MAC address.
        rName : str
            Human-readable name for this device. Used in reporting.
        iTime : int
            Unixtime of current batch, to the nearest whole second.
        iOctetsRX : int
            Number of octets transmitted to this device during the current time 
            period (1 second duration)
        iOctetsTX : int
            Number of octets received from this device during the current time 
            period (1 second duration)
        sBuffer : collections.deque
            Sequence of previous readings. Unbounded. Each item in the sequence 
            consists of a 3-tuple, (iTime, iOctetsRX, iOctetsTX) recorded at 
            the end of a sampling period. Thus the current time cannot appear 
            in this sequence.
        rRRDPath : str
            File-system path to Round-Robin Database (RRD) file into which 
            samples are persisted.
    '''
    # -------------------------------------------------------------------------
    def __init__(self, rID, rName):
        self.rID = rID
        self.rRRDPath = os.path.join(grDBPath, rID) + os.extsep + "rrd"
        self.rName = rName
        self.iTime = 0
        self.iOctetsRX = 0
        self.iOctetsTX = 0
        self.sBuffer = collections.deque()

    # -------------------------------------------------------------------------
    def _bank(self, iTime):
        # Guarantees that self.iTime matches the incoming iTime, possibly 
        # pushing the current sample to self.sBuffer to make this so.
        #
        # Always call this before incrementing self.iOctetsRX and 
        # self.iOctetsTX
        if self.iTime == 0:
            # First reading
            self.iTime = iTime

        elif self.iTime < iTime:
            if self.iOctetsRX or self.iOctetsTX:
                # Skip blank readings (so the mtime on the RRD file can be used 
                # to see when the last update was)
                sSample = Sample(self.iTime, self.iOctetsRX, self.iOctetsTX)
                self.sBuffer.append( sSample )
            self.iTime = iTime
            self.iOctetsRX = 0
            self.iOctetsTX = 0

    # -------------------------------------------------------------------------
    def record_rx(self, iTime, iOctets):
        self._bank(iTime)
        self.iOctetsRX += iOctets

    # -------------------------------------------------------------------------
    def record_tx(self, iTime, iOctets):
        self._bank(iTime)
        self.iOctetsTX += iOctets

    # -------------------------------------------------------------------------
    def get_stats(self):
        # Retrieve mean bytes per second over the last 10+ seconds (hint: 
        # rrdgraph has a PRINT feature that can probably be used)
        import math

        fRX = 0.0
        fTX = 0.0

        iTotalRX = 0
        iTotalTX = 0
        fStart = float("+inf")
        fEnd = float("-inf")
        for sSample in self.sBuffer:
            fStart = min(fStart, sSample.iTime)
            fEnd = max(fEnd, sSample.iTime)
            iTotalRX += sSample.iOctetsRX
            iTotalTX += sSample.iOctetsTX

        fDuration = fEnd - fStart
        if fDuration == 0:
            fDuration = 1
        if not math.isinf(fDuration):
            fRX = iTotalRX / fDuration / 1024
            fTX = iTotalTX / fDuration / 1024

        return "%3.0f kiB/s TX    %3.0f kiB/s RX   %s   %s" % (
                fTX, fRX, self.rID, self.rName)

    # -------------------------------------------------------------------------
    def flush(self, iTime):
        import subprocess

        # Persist all samples older than iTime
        self._bank(iTime)

        if not os.path.exists( self.rRRDPath ):
            self._create_rrd()

        lData = []
        while self.sBuffer:
            sSample = self.sBuffer.popleft()
            rData = ':'.join(str(x) for x in sSample)
            lData.append(rData)

            if len(lData) > 20:
                self._update_rrd(lData)
                lData = []

        if lData:
            self._update_rrd(lData)

    # -------------------------------------------------------------------------
    def _update_rrd(self, lData):
        import subprocess
        subprocess.check_call([
                "rrdtool",
                    "update", self.rRRDPath,
                    "--daemon", "unix:"+grRRDCacheDaemon,
                    ] + lData,
                )

    # -------------------------------------------------------------------------
    def _create_rrd(self):
        import subprocess
        subprocess.check_call([
                "rrdtool",
                    "create", self.rRRDPath,
                    "--step", "1",
                    "--no-overwrite",

                    # Hearbeat: 1
                    # Min: 0
                    # Max: 50 Mbyte/s
                    "DS:rx:ABSOLUTE:1:0:50000000",
                    "DS:tx:ABSOLUTE:1:0:50000000",

                    # X-Files factor: 99% UNKNOWN is still considered known 
                    # overall

                    # 1s (1s) granularity for 1h (3600s)
                    "RRA:AVERAGE:.99:1:3600",

                    # 1m (60s) granularity for 48h (2880m)
                    "RRA:AVERAGE:.99:60:2880",

                    # 1h (3600s) for 52w (8736h)
                    "RRA:AVERAGE:.99:3600:8736",

                    # 6h (21600s) for 5 years (24960 x 6h)
                    "RRA:AVERAGE:.99:21600:24960",
                ])

# -----------------------------------------------------------------------------
def spooler(iFD, fTimeout):
    '''
    Yield complete lines (including trailing newlines) from the file descriptor 
    iFD, or an empty string if fTimeout seconds have elapsed without any data 
    becoming available.

    Raises StopIteration if the file-descriptor is closed.

    :Parameters:
        iFD : int
            File-descriptor number, as returned from os.open() and 
            file.fileno()
        fTimeout : float, seconds
            Number of seconds to wait for data before returning an empty 
            string. This guarantees that any for loop iterating this spooler 
            runs at least every fTimeout seconds. Good for, e.g., progress 
            bars.

    :Raises StopIteration: File descriptor has been closed
    '''
    import os
    import select

    tArgs = ( (iFD,), (), (), fTimeout)

    rIncompleteLine = ''
    while True:
        # Wait until data is available to read, or time out has elapsed
        tRead, tWrite, tErr = select.select( *tArgs )

        if not tRead:
            yield ''

        rData = os.read(iFD, 4096)

        if not rData:
            # NB: This raises a StopIteration exception because this function 
            # is a generator due to the presence of the yield statement below.
            return

        for rLine in rData.splitlines(True):    # keepends=True
            if rLine[-1] == '\n':
                if rIncompleteLine:
                    rLine = rIncompleteLine + rLine
                    rIncompleteLine = ''
                yield rLine
            else:
                # Not a complete line, indicating that there was more data to 
                # retrieve than fit in our read() buffer
                rIncompleteLine += rLine

# -----------------------------------------------------------------------------
def parse_record(rRecord):
    '''
    Parse a single line of output from ``tcpdump`` into:

        * iTime: Unixtime of record, to nearest second
        * iMACSource: MAC address of device that transmitted this packet
        * iMACDestination: MAC address of device this packet is headed to
        * iLength: Packet length in octets, including overheads (e.g. headers)

    Sample record::
        
        1403634415.609416 b8:27:eb:8f:c0:f3 > 60:45:bd:9c:9d:bc, ethertype IPv4 (0x0800), length 1378: 8.254.195.126.80 > 192.168.1.225.6135: Flags [.], seq 145640:146964, ack 1, win 54, length 1324

    Sample output:

        (1403634415, 202481595302131L, 105852650167740L, 1378)

    :Raises ValueError: Cannot parse line.
    '''
    iTime = int(rRecord[0:10])

    iMACSource = 0
    iMACSource += int(rRecord[18:20], 16) << (5*8)
    iMACSource += int(rRecord[21:23], 16) << (4*8)
    iMACSource += int(rRecord[24:26], 16) << (3*8)
    iMACSource += int(rRecord[27:29], 16) << (2*8)
    iMACSource += int(rRecord[30:32], 16) << (1*8)
    iMACSource += int(rRecord[33:35], 16) << (0*8)

    iMACDestination = 0
    iMACDestination += int(rRecord[38:40], 16) << (5*8)
    iMACDestination += int(rRecord[41:43], 16) << (4*8)
    iMACDestination += int(rRecord[44:46], 16) << (3*8)
    iMACDestination += int(rRecord[47:49], 16) << (2*8)
    iMACDestination += int(rRecord[50:52], 16) << (1*8)
    iMACDestination += int(rRecord[53:55], 16) << (0*8)

    iLength = int(rRecord[70:rRecord.index(':', 70)])

    sRecord = Record(iTime, iMACSource, iMACDestination, iLength)

    return sRecord

# -----------------------------------------------------------------------------
def parse_MAC(rMAC):
    return int(rMAC, 16)

# -----------------------------------------------------------------------------
def format_MAC(iMAC):
    return ('%012x' % iMAC)

# -----------------------------------------------------------------------------
def get_device_names():
    # Return a mapping from MAC addresses (integers) to human-readable names 
    # (strings)
    import os
    dLookup = {}
    rFile = os.path.expanduser(grDeviceNames)
    with file(rFile, 'r') as sFH:
        for rLine in iter(sFH.readline, ''):
            rLine = rLine.strip()
            if not rLine:
                continue
            rMAC, _, rName = rLine.partition(' ')
            rMAC = rMAC.strip()
            iMAC = int(rMAC, 16)
            rName = rName.strip()

            dLookup[iMAC] = rName

    return dLookup

# -----------------------------------------------------------------------------
def is_unicast(iMAC):
    # Returns False if MAC is known to be a special address, such as multicast 
    # and broadcast traffic. True otherwise.
    #
    # The first octet in the MAC address can be used to determine multicast 
    # status: if the least significant bit is 1 it is multicast, unicast 
    # otherwise.

    return (iMAC >> (5*8)) & 1 == 0

    # Rules are based on 
    # http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml

    # Broadcast
    if iMAC == 0xffffffFFFFFF:
        return False

    # IPv4 Multicast
    elif iMAC >> 24 == 0x01005e:
        return False

    # IPv6 Multicast
    elif iMAC >> 32 == 0x3333:
        return False

    # Virtual Router Redundancy Protocol
    elif iMAC >> 8 == 0x00005e0001:
        return False

    else:
        return True

# -----------------------------------------------------------------------------
def main():
    '''
    :Variables:
        dDevices : long -> Device mapping
            Mapping from Ethernet MAC addresses to `Device` instances. MAC 
            addresses are represented as integer numbers. So 12:34:56:78 is 
            represented as 0x12345678 (305419896 in decimal)
    '''
    import sys
    import time
    import subprocess

    dDevices = {}
    dMAC2Name = get_device_names()

    sPH = subprocess.Popen(
            ['sudo', 'tcpdump',
                '-i', grInterface,  # Interface
                '-l',               # Line-buffered
                '-e',               # Print link-level headers
                '-tt',              # Unformatted timestamps (unixtime)
                '-q',               # Quick (less detail)
                '-n'],              # Numeric: Skip DNS resolution
            bufsize=1,              # Line-buffered
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=True,
            )

    sPH.stdin.close()
    iFD = sPH.stdout.fileno()
    siLines = spooler(iFD, 3.0)

    iNextTick = int(time.time() + 3)

    for rLine in siLines:
        if rLine:
            try:
                sRecord = parse_record(rLine)
            except ValueError:
                print 'AssertionError: Unable to parse TCP dump output:', rLine

            # Ignore broadcast and multicast traffic, since it doesn't 
            # contribute to internet usage (assumption: we are behind a NAT, 
            # and so do not participate in multicast)
            if (not is_unicast(sRecord.iMACSource)
                    or not is_unicast(sRecord.iMACDestination)):
                continue

            if sRecord.iMACSource not in dDevices:
                rID = format_MAC(sRecord.iMACSource)
                rName = dMAC2Name.get(sRecord.iMACSource, '')
                sDevice = Device(rID, rName)
                dDevices[sRecord.iMACSource] = sDevice
            else:
                sDevice = dDevices[sRecord.iMACSource]

            sDevice.record_tx( sRecord.iTime, sRecord.iLength )

            if sRecord.iMACDestination not in dDevices:
                rID = format_MAC(sRecord.iMACDestination)
                rName = dMAC2Name.get(sRecord.iMACDestination, '')
                sDevice = Device(rID, rName)
                dDevices[sRecord.iMACDestination] = sDevice
            else:
                sDevice = dDevices[sRecord.iMACDestination]

            sDevice.record_rx( sRecord.iTime, sRecord.iLength )
        else:
            print 'Timeout'
            time.sleep(1)

        if sRecord.iTime > iNextTick:
            iNextTick = sRecord.iTime + 3

            if sys.stdout.isatty():
                # If running on a console, display current activity (mean bytes 
                # per second)
                sys.stdout.write('\033[0;0H')  # Move cursor to 0,0
                sys.stdout.write('\033[2J')    # Clear entire display
                for rDeviceID in sorted(dDevices):
                    print dDevices[rDeviceID].get_stats()

            # Flush device instances (except data from current second)
            for sDevice in dDevices.values():
                sDevice.flush(sRecord.iTime)


# =============================================================================
if __name__ == '__main__':
    main()
