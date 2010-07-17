#!/usr/bin/env python
# Ping the upstream gateway (i.e. ISP)

def get_gateway_ip():
    password=""
    modem_ip="192.168.1.1"

    try:
        import socket
        import time

        sock = socket.socket()

        for i in range(10):
            try:
                sock.connect( (modem_ip, 23) )
                break
            except socket.error, e:
                if e.args[0] == 111:
                    # 111: Connection refused
                    time.sleep(1)
                else:
                    raise

        sock.sendall(password+"\nip route status\nexit\n")

        # Example response
        #
        # Password: ******
        # Copyright (c) 1994 - 2007 ZyXEL Communications Corp.
        # P-660R-D1> ip route status 
        # Dest            FF Len Device     Gateway         Metric stat Timer  Use
        # 195.166.128.242 00 32  mpoa00     195.166.128.242   1    03a9 0      159
        # 192.168.1.0     00 24  enet0      192.168.1.1       1    041b 0      521464
        # default         00 0   mpoa00     MyISP             2    00ab 0      536113
        # P-660R-D1> exit
        # 
        s = ""
        while " enet0 " not in s:
            p = sock.recv(4096)
            if p == "": break
            s += p
            time.sleep(0.02)
        sock.shutdown(socket.SHUT_WR|socket.SHUT_RD)
        sock.close()

        for line in s.replace("\r", "").split("\n"):
            # Field starter bytes
            #                 15     22                           52        61
            #                 |      |                            |         |
            # 195.166.128.242 00 32  mpoa00     195.166.128.242   1    03a9 0      159
            # |                  |              |                      |           |
            # 0                  18             34                     56          68
            d = dict()
            d["Dest"] = line[:15].strip()
            d["FF"] = line[15:18].strip()
            d["Len"] = line[18:22].strip()
            d["Device"] = line[22:34].strip()
            d["Gateway"] = line[34:52].strip()
            d["Metric"] = line[52:56].strip()
            d["stat"] = line[56:61].strip()
            d["Timer"] = line[61:68].strip()
            d["Use"] = line[68:].strip()

            if d["FF"] != "00":
                # Not a routing table entry (or at least, not a normal one)
                continue

            if d["Device"] == "mpoa00" and d["Dest"] == d["Gateway"]:
                # Default WAN route
                return d["Gateway"]

    except EOFError:
        s.close()

def get_avg_ping_gw():
    import os

    ip = get_gateway_ip()

    # Options:
    #   -q      Quiet (only header + summary lines)
    #   -n      Numeric (don't perform reverse DNS)
    #   -l 3    Allow up to 3 outsanding ping packets at once
    #   -w 20   Exit after 20 seconds, no matter what
    #   -Q 0x10 Quality of Service set to Low Latency
    cmd = "ping -q -n -l 3 -w 20 -Q 0x10 %s | grep ^rtt"  % ip
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
