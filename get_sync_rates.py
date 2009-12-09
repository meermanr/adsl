#!/usr/bin/env python
# Query the current ADSL WAN sync speed of my ZyXEL ADSL Modem

def get_up_and_down_sync_rates():
	password=""
	modem_ip="192.168.1.1"

	up = None
	down = None

	try:
		import socket
		import time
		sock = socket.socket()
		sock.connect( (modem_ip, 23) )
		sock.sendall(password+"\nwan adsl chandata\nexit\n")
		s = ""
		while "far-end fast channel bit rate: " not in s:
			s += sock.recv(4096)
		sock.shutdown(socket.SHUT_WR|socket.SHUT_RD)
		sock.close()

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

	if up:
		up = int(up)

	if down:
		down = int(down)

	return (up, down)

if __name__ == "__main__":
	# Suitable for RRDtool
	up, down = get_up_and_down_sync_rates()
	print "%s:%s" % (up or "U", down or "U")
