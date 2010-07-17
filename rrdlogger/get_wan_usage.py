#!/usr/bin/env python
# Ping the upstream gateway (i.e. ISP)

def get_wan_in_out():
    password=""
    modem_ip="192.168.1.1"

    up = None
    down = None

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

        sock.sendall(password+"\nip ifconfig wanif0\nexit\n")
        # Example response
        #
        # Password: ******
        # Copyright (c) 1994 - 2007 ZyXEL Communications Corp.
        # P-660R-D1> ip ifconfig wanif0
        # wanif0: mtu 1500 
        #     inet 81.174.133.76, netmask 0xffffffff, broadcast 255.255.255.255
        #     RIP RX:None, TX:None, 
        #     [InOctets      78310527] [InUnicast    118209] [InMulticast            0]
        #     [InDiscards           0] [InErrors          0] [InUnknownProtos        0]
        #     [OutOctets     16230351] [OutUnicast   116621] [OutMulticast           0]
        #     [OutDiscards          0] [OutErrors         0]
        # P-660R-D1> exit
        s = ""
        while " [OutErrors " not in s:
            p = sock.recv(4096)
            if p == "": break
            s += p
            time.sleep(0.02)
        sock.shutdown(socket.SHUT_WR|socket.SHUT_RD)
        sock.close()

        downloaded = 0
        uploaded = 0
        for line in s.replace("\r", "").split("\n"):
            if "InOctets" in line:
                downloaded = int(line[13:27].strip())
            elif "OutOctets" in line:
                uploaded = int(line[14:27].strip())

        return uploaded, downloaded

    except EOFError:
        s.close()

if __name__ == "__main__":
    print "%s:%s" % get_wan_in_out()
