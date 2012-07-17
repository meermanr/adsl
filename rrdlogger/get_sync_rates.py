#!/usr/bin/env python
# Query the current ADSL WAN sync speed of my ZyXEL ADSL Modem

def get_up_and_down_sync_rates():
    username="admin"
    password=None
    modem_ip="192.168.1.254"

    if modem_pass is None:
        import os
        p = os.path.abspath( __file__ )
        p = os.path.dirname(p)
        p = os.path.join(p, "..", ".password")
        with file(p, "rU") as fh:
            modem_pass = fh.read().strip()

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
        c.write("port a1 show\n")

        # Example output:
        #
        # LocalFastChannelRxRate                             = 3264000
        # LocalFastChannelTxRate                             = 448000

        c.read_until("LocalFastChannelRxRate                             = ")
        down = c.read_until("\n").strip()

        c.read_until("LocalFastChannelTxRate                             = ")
        up = c.read_until("\n").strip()

    finally:
        c.close()

    if up:
        up = int(up) / 1024     # B/s -> kB/s
    else:
        up = "U"

    if down:
        down = int(down) / 1024 # B/s -> kB/s
    else:
        down = "U"

    return (up, down)

if __name__ == "__main__":
    # Suitable for RRDtool
    up, down = get_up_and_down_sync_rates()
    print "%s:%s" % (up, down)
