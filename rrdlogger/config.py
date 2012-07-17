#!/usr/bin/env python
import os

s = os.path.abspath( __file__ )
s = os.path.dirname(s)

mi = os.path.join(s, ".modem_ip")
mu = os.path.join(s, ".modem_user")
mp = os.path.join(s, ".modem_pass")

pu = os.path.join(s, ".plusnet_user")
pp = os.path.join(s, ".plusnet_pass")

with file(mi, "rU") as fh:
    modem_ip = fh.read().strip()
with file(mu, "rU") as fh:
    modem_user = fh.read().strip()
with file(mp, "rU") as fh:
    modem_pass = fh.read().strip()

with file(pu, "rU") as fh:
    plusnet_user = fh.read().strip()
with file(pp, "rU") as fh:
    plusnet_pass = fh.read().strip()
