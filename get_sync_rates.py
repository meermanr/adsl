#!/usr/bin/env python
# Query the current ADSL WAN sync speed of my ZyXEL ADSL Modem

def get_up_and_down_sync_rates():
	password=""
	modem_ip="192.168.1.1"

	import telnetlib

	up = None
	down = None

	try:
		tn = telnetlib.Telnet(modem_ip, 23, 5)
		tn.read_until("Password: ", 5)
		tn.write(password + "\n")
		tn.read_until("modem> ", 5)
		tn.write("wan adsl chandata\n")
		s = tn.expect(["modem> "])[2]
		tn.write("exit\n")
		tn.read_all()

		for line in s.replace("\r", "").split("\n"):
			rate = None
			try:
				rate = int(line.split(":")[1].replace(" kbps", "").strip())
			except: pass

			if line.startswith("near-end"):
				down = max(down, rate)
			if line.startswith("far-end"):
				up = max(up, rate)

	except EOFError:
		tn.close()

	return (int(up), int(down))

if __name__ == "__main__":
	print "%d\t%d" % get_up_and_down_sync_rates()
