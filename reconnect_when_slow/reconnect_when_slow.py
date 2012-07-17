#!/usr/bin/env python

modem_ip = "192.168.1.1"
modem_pass = None
sync_down_lower_limit = 2500

import re
import sys

if modem_pass is None:
    import os
    p = os.path.abspath( __file__ )
    p = os.path.dirname(p)
    p = os.path.join(p, "..", ".password")
    with file(p, "rU") as fh:
        modem_pass = fh.read().strip()

def shell(cmd):
	import os
	p = os.popen(cmd)
	stdout = p.read()
	return_code = p.close()
	return stdout

def reconnect_if_too_slow():
	data = shell(""" rrdtool fetch adsl.rrd MIN -s "now - 20min" -e "now - 10min" """)
	tokens = []
	timestamp_pattern = "^(\d+):"		# '1261310700'
	value_pattern = "(nan|[.0-9e+-]+)"	# 'nan' or '3.7760000000e+03'
	tokeniser_pattern = "%s %s %s %s" % (
		timestamp_pattern,
		value_pattern,
		value_pattern,
		value_pattern
		)

	sync_down_stable_value = None
	for line in data.split("\n"):
		m = re.match(tokeniser_pattern, line)
		if m:
			time, sync_down, sync_up, ip_profile = m.groups()
			if "nan" in [sync_down, sync_up, ip_profile]:
				# Abort - general connectivity fault
				print "ERROR: General connectivity fault (NaN values in data)"
				sys.stdout.flush()
				return

			# Parse numbers ("3.776+03" -> 3776.0)
			time = eval(time)
			sync_down = eval(sync_down)
			sync_up = eval(sync_up)
			ip_profile = eval(ip_profile)

			if sync_down_stable_value is None:
				sync_down_stable_value = sync_down
			elif sync_down_stable_value != sync_down:
				print "Line speed is unstable (recently changed from %d to %d), will not force reconnect." % (sync_down_stable_value, sync_down)
				sys.stdout.flush()
				return

	print "Line speed is a stable %d" % sync_down_stable_value
	sys.stdout.flush()
	if sync_down_stable_value < sync_down_lower_limit:
		print "This is lower than %d, will force reconnect." % sync_down_lower_limit
		sys.stdout.flush()

		import socket
		sock = socket.socket()
		sock.connect( (modem_ip, 23) )
		sock.sendall(modem_pass+"\nwan adsl reset\nhelp\nexit\n")
		s = ""
		while "Valid commands are:" not in s:
			s += sock.recv(4096)
		print s
		sys.stdout.flush()
		sock.shutdown(socket.SHUT_WR|socket.SHUT_RD)
		sock.close()

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
		reconnect_if_too_slow()
		time.sleep(interval)
