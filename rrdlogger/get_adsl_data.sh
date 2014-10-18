#!/bin/bash
WAN_DATA=$(./get_wan_usage.sh | tr -d "\r")
echo "U:U:$WAN_DATA:U:U:U:U:U:U"
