#!/usr/bin/env python

import subprocess
from textwrap import dedent

adsl = [
    "DEF:sync_down_kbps=adsl.rrd:sync_down:MIN",
    "DEF:sync_up_kbps=adsl.rrd:sync_up:MIN",
	"DEF:ip_profile_kbps=adsl.rrd:ip_profile:MIN",
	"DEF:gw_ping_ms=adsl.rrd:gw_ping:MIN",
	"DEF:wan_down_bytes=adsl.rrd:wan_down:MAX",
	"DEF:wan_up_bytes=adsl.rrd:wan_up:MAX",

	"CDEF:sync_down=sync_down_kbps,1000,*",
	"CDEF:sync_up=sync_up_kbps,1000,*,-1,*",
	"CDEF:ip_profile=ip_profile_kbps,1000,*",
	"CDEF:gw_ping=gw_ping_ms,50000,*",
    "CDEF:wan_down=wan_down_bytes,8,*",
    "CDEF:wan_up=wan_up_bytes,8,*,-1,*",

	"AREA:sync_down#ffcc99:Connection speed (bit/s)",
	"AREA:wan_down#009900:Download use (bit/s)",
	"AREA:wan_up#ff0000:Upload use (bit/s)",
	"LINE2:ip_profile#000099:ISP Limit (bit/s)",
	"LINE:gw_ping#cc0000:Gateway Latency (1M == 20ms)",
    ]

periods = [
    # [Name, Start, End]
	["Last 2 hours", "now - 2 hours", "now"],
	["Today", "00:00", "23:59"],
	["Yesterday", "00:00 - 24 hours", "23:59 - 24 hours"],
	["This week", "00:00 Sunday", "00:00 Sunday + 1 week"],
	["Last week", "00:00 Sunday - 1 week", "00:00 Sunday"],
	["Last 4 weeks", "now - 4 week", "now"],
	["Last 6 months", "now - 6 months", "now"],
    ]

for title, start, end in periods:
    safe_title = title.replace(" ", "_")
    filename = "images/g_{0}.png".format(safe_title)
    cmd = [
        "rrdtool", "graph", filename,
        "--start", start,
        "--end", end,
        "--title", title,
        "--lower-limit=0",
        "--upper-limit", "6000000",
        "--rigid",
        "--width", "800",
        "--height", "200",
        "--imgformat", "PNG",
        ] + adsl
    print cmd
    subprocess.check_call(cmd)
