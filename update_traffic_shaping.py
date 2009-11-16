#!/usr/bin/env python

from get_plusnet_stable_rate import get_ip_profile
from get_sync_rates import get_up_and_down_sync_rates
import os

(up_sync, down_sync) = get_up_and_down_sync_rates()
down_limit = get_ip_profile()

up = int(0.7 * up_sync)
down = int(0.7 * min(down_sync, down_limit))

print "  Sync speeds: %s up / %s down" % (str(up_sync).rjust(3, " "), str(down_sync).rjust(4, " "))
print "   IP profile:          %s down" % str(down_limit).rjust(4, " ")
print "Traffic shape: %s up / %s down" % (str(up).rjust(3, " "), str(down).rjust(4, " "))

os.system("sudo wondershaper eth1 %d %d" % (down, up))
