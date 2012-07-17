#!/usr/bin/env python
# Ping the upstream gateway (i.e. ISP)

import config

def get_wan_in_out():
    import telnetlib

    up = None
    down = None

    try:
        c = telnetlib.Telnet(config.modem_ip)

        c.read_until("Login: ")
        c.write(config.modem_user+"\n")

        c.read_until("Password: ")
        c.write(config.modem_pass+"\n")

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
