#!/usr/bin/env python

import os
import sys
import glob
import time
import cgitb
import subprocess

import rhodes

from textwrap import dedent

cgitb.enable()
print "Content-type: text/html"
print
sys.stdout.flush()

os.umask(0002)  # Full group access

iHorizon = time.time() - (3600*8)

lDevices = []
for rDB in sorted(glob.glob("*.rrd")):
    if os.stat(rDB).st_mtime < iHorizon:
        continue

    lDeviceDescription = [
        "DEF:rx=%s:rx:AVERAGE" % rDB,
        "DEF:raw_tx=%s:tx:AVERAGE" % rDB,

        "CDEF:tx=raw_tx,-1,*",

        "AREA:rx#1100bb:Download (bytes/s)",
        "AREA:tx#bb0000:Upload (bytes/s)",
        ]
    tEntry = (rDB.rpartition('.')[0], lDeviceDescription)
    lDevices.append(tEntry)

periods = [
    # [Name, Start, End]
	["Last 8 hours", "now - 8 hours", "now"],
	#["Last 48 hours", "now - 48 hours", "now"],
	#["Today", "00:00", "23:59"],
	#["Yesterday", "00:00 - 24 hours", "23:59 - 24 hours"],
	#["This week", "00:00 Sunday", "00:00 Sunday + 1 week"],
	#["Last week", "00:00 Sunday - 1 week", "00:00 Sunday"],
    #["Last 4 weeks", "now - 4 week", "now"],
    #["Last 7 days", "now - 7 days", "now"],
    #["Last 6 months", "now - 6 months", "now"],
    #["Last 2 years", "now - 2 years", "now"],
    ]

dDeviceNames = rhodes.get_device_names()

print "<html><head><title>LAN Usage by MAC</title></head><body>"
print "<p>As at %s</p>" % time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
sys.stdout.flush()

for rPeriodName, start, end in periods:
    print "<h2>{0}</h2>".format(rPeriodName)
    sys.stdout.flush()

    for rMAC, lDeviceDescription in lDevices:
        iMAC = rhodes.parse_MAC(rMAC)
        rDeviceName = dDeviceNames.get(iMAC, rMAC)
        rTitle = "{0}, {1}".format(rPeriodName, rDeviceName)
        rSafeTitle = rTitle.replace(" ", "_")
        filename = "images/g_{0}.png".format(
                rSafeTitle.replace(' ', '_').replace(',', '_'))

        lCMD = [
                "rrdtool", "flushcached", rMAC + ".rrd", 
                "--daemon", "unix:./rrdcached.sock",
                ]
        subprocess.check_call(lCMD)

        lCMD = [
            "rrdtool", "graph", filename,
            "--start", start,
            "--end", end,
            "--vertical-label", "bytes/s",
            "--title", rTitle,
            "--lazy",
            "--width", "1024",
            "--height", "200",
            "--imgformat", "PNG",
            "--imginfo", """<img src="images/%s" width="%lu" height="%lu" alt="{0}">""".format(rTitle)
            ] + lDeviceDescription
        subprocess.check_call(lCMD)
        sys.stdout.flush()

print "</body></html>"
