#!/usr/bin/env python
# vim: set expandtab autoindent tabstop=4 softtabstop=4 shiftwidth=4:
# Ping the upstream gateway (i.e. ISP)
import sys
import config

def get_gateway_ip():
    import subprocess
    import time
    """
    (echo -e 'admin\nCP1421VFF58\n:ip rtlist\nexit\n'; sleep 1 ) | telnet 192.168.1.254 | sed -ne '/\/32 Internet/{s/^\s*//; s/\/.*$//; p}'
    """
    cmd = ['telnet', config.modem_ip]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(config.modem_user+"\n")
    p.stdin.write(config.modem_pass+"\n")
    p.stdin.write(":ip rtlist\n")
    time.sleep(1)
    s = p.stdout.read().strip()
    p.close()
    print p
    import telnetlib

    try:
        c = telnetlib.Telnet(config.modem_ip)

        c.read_until("Login: ")
        c.write(config.modem_user+"\n")

        c.read_until("Password: ")
        c.write(config.modem_pass+"\n")

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
        ip = c.read_until("\n").strip()

        if sys.stdout.isatty():
            print "Gateway IP:", ip

        return ip

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
