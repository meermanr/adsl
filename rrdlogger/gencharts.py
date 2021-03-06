#!/usr/bin/env python

import os
import sys
import time
import cgitb
import subprocess

from textwrap import dedent

cgitb.enable()
print "Content-type: text/html"
print
sys.stdout.flush()

os.umask(0002)  # Full group access

adsl = [
    "DEF:sync_down=adsl.rrd:sync_down:AVERAGE",
    "DEF:sync_up=adsl.rrd:sync_up:AVERAGE",
	"DEF:ip_profile_kbps=adsl.rrd:ip_profile:MIN",
	"DEF:gw_ping_ms=adsl.rrd:gw_ping:AVERAGE",
	"DEF:wan_down_bytes=adsl.rrd:wan_down:AVERAGE",
	"DEF:wan_up_bytes=adsl.rrd:wan_up:AVERAGE",
    "DEF:attn_down_db=adsl.rrd:attn_down:AVERAGE",
    "DEF:attn_up_db=adsl.rrd:attn_up:AVERAGE",
    "DEF:snr_down_db=adsl.rrd:snr_down:AVERAGE",
    "DEF:snr_up_db=adsl.rrd:snr_up:AVERAGE",
    "DEF:sys_uptime_ms=adsl.rrd:sys_uptime:AVERAGE",
    "DEF:session_lastchange_ms=adsl.rrd:session_lastchange:AVERAGE",
    "DEF:temp_c=adsl.rrd:temp:AVERAGE",

	"CDEF:ip_profile=ip_profile_kbps,1000,*",
	"CDEF:gw_ping=gw_ping_ms,900,TREND,50000,*",
    "CDEF:wan_down=wan_down_bytes,8,*",
    "CDEF:wan_up=wan_up_bytes,8,*,-1,*",
    "CDEF:attn_down=attn_down_db,10000,*",
    "CDEF:attn_up=attn_up_db,10000,*",
    "CDEF:snr_down=snr_down_db,10000,*",
    "CDEF:snr_up=snr_up_db,10000,*",
    "CDEF:temp=temp_c,100000,*",

	"AREA:sync_down#eeeeee:Connection speed (bit/s)",
	"AREA:wan_down#009900:Download use (bit/s)",
	"AREA:wan_up#ff0000:Upload use (bit/s)",
	"LINE2:ip_profile#000099:ISP Limit (bit/s)",
	"LINE:gw_ping#cc8800:Gateway Latency (1M == 20ms)",
    "LINE:attn_down#9999ff:Atn Down (dB)",
    "LINE:attn_up#9999ff:Atn Up (dB):dashes",
    "LINE:snr_down#00ffff:SnR Down (dB)",
    "LINE:snr_up#00ffff:SnR Up (dB):dashes",
    "LINE:temp#ff00ff:Temperature (C)",
    ]

periods = [
    # [Name, Start, End]
	#["Last 8 hours", "now - 8 hours", "now"],
	#["Last 48 hours", "now - 48 hours", "now"],
	["Today", "00:00", "23:59"],
	["Yesterday", "00:00 - 24 hours", "23:59 - 24 hours"],
	#["This week", "00:00 Sunday", "00:00 Sunday + 1 week"],
	#["Last week", "00:00 Sunday - 1 week", "00:00 Sunday"],
    #["Last 4 weeks", "now - 4 week", "now"],
    ["Last 7 days", "now - 7 days", "now"],
    ["Last 6 months", "now - 6 months", "now"],
    ["Last 2 years", "now - 2 years", "now"],
    ]

print "<html><head><title>ADSL</title></head><body>"
print "<p>As at %s</p>" % time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
sys.stdout.flush()

for title, start, end in periods:
    safe_title = title.replace(" ", "_")
    filename = "images/g_{0}.png".format(safe_title)
    cmd = [
        "rrdtool", "graph", filename,
        "--start", start,
        "--end", end,
        "--vertical-label", "bit/s",
        "--right-axis", "0.00001:0",
        "--right-axis-label", "dB or C",
        "--title", title,
        # "--lower-limit", "-1000000",
        # "--upper-limit", "6000000",
        # "--rigid",      # Do not accommodate values > upper-limit
        "--lazy",
        "--width", "1024",
        "--height", "200",
        "--imgformat", "PNG",
        "--imginfo", """<img src="images/%s" width="%lu" height="%lu" alt="{0}">""".format(title)
        ] + adsl
    subprocess.check_call(cmd)
    sys.stdout.flush()

print "<img src='http://www.thinkbroadband.com/ping/share-large/e70bac4c482ae6dafcc89986e3447a3c.png'/>"
print "</body></html>"
