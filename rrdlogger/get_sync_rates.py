#!/usr/bin/env python
# vim: set expandtab autoindent tabstop=4 softtabstop=4 shiftwidth=4:
# Query the current ADSL WAN sync speed of my ZyXEL ADSL Modem

import re
import socket
import subprocess

from textwrap import dedent

lHeadings = [
        ("DSP Firmware Version", "firmware"),
        ("Connected", "online"),
        ("Operational Mode", "mode"),
        ("Upstream", "up"),
        ("Downstream", "down"),
        ("Elapsed Time", "duration"),
        ("SNR Margin(Upstream)", "noise_up"),
        ("SNR Margin(Downstream)", "noise_down"),
        ("Line Attenuation(Upstream)", "attn_up"),
        ("Line Attenuation(Downstream)", "attn_down"),
        ("CRC Errors(Upstream)", "errors_up"),
        ("CRC Errors(Downstream)", "errors_down"),
        ]
lPatterns = []
for rTitle, rKey in lHeadings:
    rPattern = """<tr><td class="title"[^>]*>{0}</td><td>(?P<{1}>[^<]*)</td></tr>""".format(
            re.escape(rTitle),
            rKey,
            )
    lPatterns.append( rPattern )

rPattern = ".*?".join( lPatterns )
sPatternExtract = re.compile(rPattern)

def get_adsl_status():
    import config

    html = subprocess.Popen(
            ["curl",
                "--silent",
                "http://{0}/status/adslstatus.html".format(config.modem_ip),
                "--user",
                "{0}:{1}".format( config.modem_user, config.modem_pass),
                ],
            stdout=subprocess.PIPE,
            ).stdout.read().strip().replace("\n", "")

    dValues = sPatternExtract.search(html).groupdict()

    return dValues

def get_up_and_down_sync_rates():
    dValues = get_adsl_status()

    up = "U"
    down = "U"
    if dValues["up"]:
        up = int(dValues["up"]) / 1024     # B/s -> kB/s

    if dValues["down"]:
        down = int(dValues["down"]) / 1024 # B/s -> kB/s

    return (up, down)

if __name__ == "__main__":
    # Suitable for RRDtool
    up, down = get_up_and_down_sync_rates()
    print "%s:%s" % (up, down)
