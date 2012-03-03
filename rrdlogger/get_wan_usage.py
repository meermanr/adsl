#!/usr/bin/env python
# Ping the upstream gateway (i.e. ISP)

def get_wan_in_out():
    username="admin"
    password=""
    modem_ip="192.168.1.254"

    import telnetlib

    up = None
    down = None

    try:
        c = telnetlib.Telnet(modem_ip)

        c.read_until("Login: ")
        c.write(username+"\n")

        c.read_until("Password: ")
        c.write(password+"\n")

        c.read_until("admin> ")
        c.write("pppoa show transport wanlink\n")

        # Example output:
        #
        # PPP Transport: wanlink
        # 
        #              Description : PPPoA WAN Link
        #                  Summary : open for IP, sent 8951458, received 1226772

        c.read_until("Summary : open for IP, sent ")
        uploaded = int( c.read_until(",").rstrip(",").strip() )

        c.read_until(" received ")
        downloaded = int( c.read_until("\n").strip() )

    finally:
        c.close()

    return uploaded, downloaded

if __name__ == "__main__":
    print "%s:%s" % get_wan_in_out()
