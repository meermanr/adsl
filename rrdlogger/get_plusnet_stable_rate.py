#!/usr/bin/env python

def get_ip_profile():
	import os
	import sys

	cmd = """curl "https://portal.plus.net/my.html?action=stable_rate" --cookie-jar ./cookiejar --cookie ./cookiejar --data 'username=meerman&authentication_realm=portal.plus.net&password=portgentil' --silent"""

	os.chdir( os.path.dirname( __file__ ) )

	if os.path.exists("cookiejar"):
		os.unlink("cookiejar")

	os.system(cmd + " >/dev/null")		# Once to get a session cookie (stored in ./cookiejar)
	p = os.popen(cmd)	# And again with cookies obtained in previous step
	html = p.read()
	p.close()

	if os.path.exists("cookiejar"):
		os.unlink("cookiejar")


	import re
	for section in re.split("</?dl>", html):
		if "Current line speed:" in section:
			for item in section.split("<dt>"):
				if "</dt>" not in item:
					continue

				key, value = item.split("</dt>")
				key = key.strip()
				if key != "Current line speed:":
					continue

				value = re.sub("<.*?>", "", value)
				value = value.strip()
				return int(value)
			break
	else:
		raise Exception("Current line speed not present, script may need updating.")

if __name__ == "__main__":
	print get_ip_profile()
