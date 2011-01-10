#!/usr/bin/env python

import re
import sys

def shell(cmd):
	import os
	p = os.popen(cmd)
	stdout = p.read()
	return_code = p.close()
	return stdout

def maintain_traffic_shape():
	info = shell("rrdtool info adsl.rrd")
	
	ip_profile = None
	sync_up = None
	for line in info.split("\n"):
		if line.startswith("ds[ip_profile].last_ds = "):
			ip_profile = int(line.split("=", 1)[1].replace('"', '').strip())

		if line.startswith("ds[sync_up].last_ds = "):
			sync_up = int(line.split("=", 1)[1].replace('"', '').strip())

		if ip_profile is not None and sync_up is not None:
			break
	
	else:
		print "Incomplete data, leaving traffic limits alone"
		print "ip_profile", ip_profile
		print "sync_up", sync_up
		return

	sync_up = int(sync_up * 0.85)
	cmd = "sudo wondershaper eth0 %d %d" % (ip_profile, sync_up)
	print cmd
	shell(cmd)

if __name__ == "__main__":
	# Find out how often readings are taken so we know how long to sleep
	step = shell("rrdtool info adsl.rrd | grep '^step = '")
	step = step.split("=")[1]
	step = float(step)

	# The interval should not be equal to `step` to prevent the logging script
	# from taking a reading during reconnection (at which time the sync rates
	# are 0/0). Running every other step guarentees that the logger gets at
	# least one new and real reading between our checks.
	interval = step * 2.0

	import time
	while True:
		maintain_traffic_shape()
		time.sleep(interval)
