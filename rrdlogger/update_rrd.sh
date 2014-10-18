#!/bin/bash -e

DB=adsl.rrd

# 10 weeks @ 5min accuracy = 10 * 7 * 24 * 12 * (5min) readings = 20160 x 1
# 1 year @ 1hour accuracy = 365 * 24 * (12 * 5min) readings = 8760 x 12
# 10 years @ 1day accuracy = 10 * 365 * (24 * 12 * 5min) readings = 3650 x 288
#
# Note that session_lastchange holds a copy of sys_uptime as it was when ADSL 
# session last changed state (i.e. reconnected). Hence its value only changes 
# when the session drops.
if [ ! -e $DB ]
then
	rrdtool create $DB \
		--step 300 \
		DS:sync_down:GAUGE:300:0:8000000 \
		DS:sync_up:GAUGE:300:0:1000000 \
		DS:wan_down:COUNTER:300:0:U \
		DS:wan_up:COUNTER:300:0:U \
        DS:attn_down:GAUGE:300:0:U \
        DS:attn_up:GAUGE:300:0:U \
        DS:snr_down:GAUGE:300:0:U \
        DS:snr_up:GAUGE:300:0:U \
        DS:sys_uptime:COUNTER:300:0:U \
        DS:session_lastchange:GAUGE:300:0:U \
		DS:ip_profile:GAUGE:900:0:8000 \
		DS:gw_ping:GAUGE:600:0:U \
		DS:temp:GAUGE:600:-50:50 \
        RRA:MIN:0.9:1:20160 \
        RRA:MIN:0.9:12:8760 \
        RRA:MIN:0.9:288:3650 \
        RRA:AVERAGE:0.5:1:20160 \
        RRA:AVERAGE:0.5:12:8760 \
        RRA:AVERAGE:0.5:288:3650 \
        RRA:MAX:0.9:1:20160 \
        RRA:MAX:0.9:12:8760 \
        RRA:MAX:0.9:288:3650
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
# The obvious solution is not to use the "N" time specifier, but rather an 
# explicit time. Care is still needed to avoid filling the database with 
# unknown value, so we store all the metrics at once. To minimise error we 
# attempt to collect metrics in parallel.
while true
do
    # Start time
    TIMESTAMP=$(date +%s)   # e.g. 1279396108

    # Run scripts in parallel, and redirect their STDOUT
    ./timelimit.py -t 20 ./get_plusnet_stable_rate.py > .last_plusnet_stable_rate &
    ./timelimit.py -t 20 ./get_adsl_data.sh > .last_adsl_data &
    ./timelimit.py -t 20 ./get_gw_ping.sh > .last_gw_ping &
    ./timelimit.py -t 20 ./get_temp.sh > .last_temp &

    wait

    ADSL=$(cat .last_adsl_data)
    BRAS=$(cat .last_plusnet_stable_rate)
    PING=$(cat .last_gw_ping)
    TEMP=$(cat .last_temp)

    [ -z "$ADSL" ] && SYNC="U:U:U:U:U:U:U:U:U:U"
    [ -z "$BRAS" ] && BRAS="U"
    [ -z "$PING" ] && PING="U"
    [ -z "$TEMP" ] && TEMP="U"

    # Update all RRD DS at once
    rrdtool update $DB \
		-t sync_down:sync_up:wan_down:wan_up:attn_down:attn_up:snr_down:snr_up:sys_uptime:session_lastchange:ip_profile:gw_ping:temp \
        $TIMESTAMP:$ADSL:$BRAS:$PING:$TEMP

        # Sleep for half the RRD's step interval, effectively feeding the RRD 
        # samples at double its internal sampling rate.
        NEXT_TIMESTAMP=$(( $TIMESTAMP + 150 ))
        NOW=$(date +%s)
        sleep $(( $NEXT_TIMESTAMP - $NOW ))
done
