#!/bin/bash

DB=adsl.rrd

# 2 weeks @ 5min accuracy = 2 * 7 * 24 * 12 * (5min) readings = 4032 x 1
# 4 weeks @ 1hour accuracy = 4 * 7 * 24 * (12 * 5min) readings = 672 x 12
# 2 months @ 1 day accuracy = 2 * 4 * 7 * (24 * 12 * 5min) readings =  56 x 288
# 6 months @ 3 day accuracy = 6 * 4 * 2 * (3.5 * 24 * 12 * 5min) readings = 48 x 1008
# 1 year @ 1 week accuracy = 12 * 4 * (7 * 24 * 12 * 5min) readings = 48 x 2016
# 10 years @ 1 month accuracy = 10 * 12 * (4 * 7 * 24 * 12 * 5min) readings = 120 x 8064
if [ ! -e $DB ]
then
	rrdtool create $DB \
		--step 300 \
		DS:sync_down:GAUGE:600:0:8000 \
		DS:sync_up:GAUGE:600:0:1000 \
		DS:ip_profile:GAUGE:600:0:8000 \
		DS:gw_ping:GAUGE:600:0:U \
		DS:wan_down:COUNTER:600:0:U \
		DS:wan_up:COUNTER:600:0:U \
		RRA:MIN:0.5:1:4032 \
		RRA:MIN:0.5:12:672 \
		RRA:MIN:0.5:288:56 \
		RRA:MIN:0.5:1008:56 \
		RRA:MIN:0.5:2016:48 \
		RRA:MIN:0.5:8064:120 \
		RRA:MAX:0.5:1:4032 \
		RRA:MAX:0.5:12:672 \
		RRA:MAX:0.5:288:56 \
		RRA:MAX:0.5:1008:56 \
		RRA:MAX:0.5:2016:48 \
		RRA:MAX:0.5:8064:120
fi

# RRD does not require that all data stores (DS) be updated at once, but in 
# practice it is the only way to get any useful data when using the "N" (now) 
# time specifier.
#
# For any timestamp created in the RRD database, any unspecified DS is quite 
# rightly assigned an UNKNOWN value. Calling `rrdtool update ... N:value` 
# multiple times will create multiple timestamps (as 'now' has a different 
# value in each invokation).
#
# For example, suppose an RRD with 4x DS and a script which uses 4x `rrdtool 
# update` invokations, one per DS, to enter values. The values recorded in the 
# RRD database are:
#
#   TIME DS1  DS2  DS3  DS4
#    0   1.2   U    U    U
#    1    U   34    U    U
#    2    U    U    3.4  U
#    3    U    U    U    89
#
# Each DS has 3x UNKNOWN and 1x value, thus each DS has >50% UNKNOWN and will 
# be ignored by `rrdtool graph` et al.
#
# One obvious solution is not to use the "N", but rather record the time as 
# TIME==0 and use that in all 4x `rrdtool update` invokations. This works, but 
# slightly misrepresents reality - if DS1 takes 20 seconds to retrieve / 
# calculate then DS2's measurement will only begin 20s after the recorded time!
#
# A better solution is to measure all DS in parallel and then update the RRD 
# with a single invokation.
while true
do
    # Start time
    TIMESTAMP=$(date +%s)   # e.g. 1279396108

    # Run scripts in parallel, and redirect their STDOUT
    ./get_plusnet_stable_rate.py > .last_plusnet_stable_rate &

    # (Cannot run these in parallel, since the router doesn't like multiple 
    # telnet sessions)
    ./get_sync_rates.py > .last_sync_rates
    ./get_wan_usage.py > .last_wan_usage
    ./get_gw_ping.py > .last_gw_ping

    wait

    SYNC=$(cat .last_sync_rates)
    PING=$(cat .last_gw_ping)
    BRAS=$(cat .last_plusnet_stable_rate)
    WANU=$(cat .last_wan_usage)

    [ -z "$SYNC" ] && SYNC="U:U"
    [ -z "$PING" ] && PING="U"
    [ -z "$BRAS" ] && BRAS="U"
    [ -z "$WANU" ] && WANU="U:U"

    # Update all RRD DS at once
    rrdtool update $DB \
        -t sync_up:sync_down:gw_ping:ip_profile:wan_up:wan_down \
        $TIMESTAMP:$SYNC:$PING:$BRAS:$WANU

        # Sleep for half the RRD's step interval, effectively feeding the RRD 
        # samples at double its internal sampling rate.
        NEXT_TIMESTAMP=$(( $TIMESTAMP + 150 ))
        NOW=$(date +%s)
        sleep $(( $NEXT_TIMESTAMP - $NOW ))
done
