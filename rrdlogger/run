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
		DS:sync_down:GAUGE:900:0:4000 \
		DS:sync_up:GAUGE:900:0:1000 \
		DS:ip_profile:GAUGE:900:0:4000 \
		RRA:MIN:0.5:1:4032 \
		RRA:MIN:0.5:12:672 \
		RRA:MIN:0.5:288:56 \
		RRA:MIN:0.5:1008:56 \
		RRA:MIN:0.5:2016:48 \
		RRA:MIN:0.5:8064:120
fi

while true
do
	rrdtool update $DB -t ip_profile:sync_up:sync_down N:$(./get_plusnet_stable_rate.py):$(./get_sync_rates.py) &
	sleep 300
	pkill -P $$	# Kill background process if not already complete
done
