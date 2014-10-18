#!/bin/bash

exec 2>/dev/null

# Get GW IP from router's PPPoE routing table
(echo -e "$(cat .modem_user)\n$(cat .modem_pass)\n:ip rtlist\nexit\n"; sleep 1 ) | telnet $(cat .modem_ip) | sed -ne '/\/32 Internet/{ s/^\s*//; s/\/.*$//;  p}' > .gw_ip
GWIP=$(cat .gw_ip)

# Options:
#   -q      Quiet (only header + summary lines)
#   -n      Numeric (don't perform reverse DNS)
#   -l 3    Allow up to 3 outsanding ping packets at once
#   -w 15   Exit after 20 seconds, no matter what
#   -Q 0x10 Quality of Service set to Low Latency
DATA=$(ping -q -n -l 3 -w 15 -Q 0x10 $GWIP | grep ^rtt)

# Example output:
#
#    1     2   3         4        5       6        7
# |-----|     |-|               |----|         |-------|
# rtt min/avg/max/mdev = 32.971/88.787/116.871/29.608 ms
#         |-|     |-----------|        |-----|
echo "$DATA" | cut -d/ -f5
