#!/usr/bin/env python
# Ping the upstream gateway (i.e. ISP)

def get_gateway_ip():
    username="admin"
    password=""
    modem_ip="192.168.1.254"

    import telnetlib

    try:
        c = telnetlib.Telnet(modem_ip)

        c.read_until("Login: ")
        c.write(username+"\n")

        c.read_until("Password: ")
        c.write(password+"\n")

        c.read_until("admin> ")
        c.write("transport show wanlink\n")

        # Example output:
        #
        # Summary Err          : 
        # Uptime               : 272397
        # Idletime             : 0
        # NCPRemote Addr       : 195.166.130.59
        # MACAddress           : 00:04:ed:bf:98:c0
        # SVC                  : false
        # Remote Atm           : 
        # Test Result          : InvaliAtm Channel
        # Tx Vci               : 38
        # Rx Vci               : 38
        # Class                : UBR
        # Port                 : a1

        c.read_until("NCPRemote Addr       : ")
        return c.read_until("\n").strip()

    finally:
        c.close()

def get_avg_ping_gw():
    import os

    ip = get_gateway_ip()

    # Options:
    #   -q      Quiet (only header + summary lines)
    #   -n      Numeric (don't perform reverse DNS)
    #   -l 3    Allow up to 3 outsanding ping packets at once
    #   -w 15   Exit after 20 seconds, no matter what
    #   -Q 0x10 Quality of Service set to Low Latency
    cmd = "/bin/bash -c 'ping -q -n -l 3 -w 15 -Q 0x10 %s | grep ^rtt'"  % ip
    p = os.popen(cmd)
    s = p.read().strip()
    p.close()

    if not s:
        return "U"  # As used by rrdtool to mean "UNKNOWN"

    # Example output:
    #
    #    0     1   2         3        4       5        6
    # |-----|     |-|               |----|         |-------|
    # rtt min/avg/max/mdev = 32.971/88.787/116.871/29.608 ms
    #         |-|     |-----------|        |-----|
    bits = s.split("/")
    assert len(bits) == 7, "%d == 7" % len(bits)
    return bits[4]

if __name__ == "__main__":
    print get_avg_ping_gw()
