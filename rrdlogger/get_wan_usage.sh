#!/bin/bash
exec 2>/dev/null

# Trying 192.168.1.254...
# Connected to 192.168.1.254.
# Escape character is '^]'.
# Username : admin
# Password : ***********
# ------------------------------------------------------------------------
# 
#       |                 |           o             |
#       |---  ,---. ,---. |---. ,---. . ,---. ,---. |     ,---. ,---.
#       |     |---' |     |   | |   | | |     |   | |     |   | |
#       `---' `---' `---' `   ' `   ' ` `---' `---' `---' `---' `
# 
#                   Technicolor TG582n FTTC
# 
#                     10.2.5.2.FO
# 
#                       Copyright (c) 1999-2012, Technicolor
# 
# 
# ------------------------------------------------------------------------
# {admin}=>:eth iflist intf=ethport4
# ethport4        : Dest: ethif4
#                   Connection State: connected  Retry: 10
#                   WAN: Enabled  Administrative MTU: 1500 Operational MTU: 1500
#                   Priority Tagging: Disabled
#                   PortNr: 1
#                   VLAN: default
#                   Tx/Rx frames: 4492963/8365577
#                   Tx/Rx octets: 367285066/2713645533
#                   Rx discarded: 0
#                   Tx/Rx multicasts: 110/108
#                   Tx/Rx broadcasts: 7/0
#                   Invalid length: 0
#                   Invalid destination address: 0
#                   Invalid VLAN id: 0
#                   Unknown protocols: 0
# {admin}=>exit

(
    echo -e "$(cat .modem_user)\n$(cat .modem_pass)\n:eth iflist intf=ethport4\nexit\n";
    sleep 1;
) \
    | telnet $(cat .modem_ip) \
    | grep octets \
    | cut -d: -f2 \
    | tr -d ' \r\n' \
    | tr '/' ' ' \
    | (
        # Swap order (adsl.rrd expects them in down (rx) up (tx) order)
        read -r TX RX
        echo $RX:$TX
     )
