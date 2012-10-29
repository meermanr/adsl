#!/usr/bin/env python

import subprocess

import config

snmp_table = [
    ["sync_down",   "transmission.94.1.1.4.1.2.3"],                 # Counter32, Bits
    ["sync_up",     "transmission.94.1.1.5.1.2.3"],                 # Counter32, Bits
    ["wan_down",    "interfaces.ifTable.ifEntry.ifInOctets.5"],     # Counter32, Octets
    ["wan_up",      "interfaces.ifTable.ifEntry.ifOutOctets.5"],    # Counter32, Octets
    ["attn_down",   "transmission.94.1.1.2.1.5.3"],                 # Guage32 dB, 440 = 44.0dB
    ["attn_up",     "transmission.94.1.1.3.1.5.3"],                 # Guage32 dB, 250 = 25.0dB
    ["snr_down",    "transmission.94.1.1.2.1.4.3"],                 # Guage32 dB, 150 = 15.0dB
    ["snr_up",      "transmission.94.1.1.3.1.4.3"],                 # Guage32 dB, 220 = 22.0dB

    ["sys_uptime",        "system.sysUpTime.sysUpTimeInstance"],           # Timeticks, 143522276 = 16 days, 14:40:22.76
    ["session_lastchange",   "interfaces.ifTable.ifEntry.ifLastChange.5"],    # Timeticks, 136924675 = 15 days, 20:20:46.75
    ]

def get_adsl_data():
    snmp_labels  = [ x[0] for x in snmp_table ]
    snmp_paths  = [ x[1] for x in snmp_table ]
    cmd = ["snmpget", "-v2c", "-c", "public", "-OvqUt", config.modem_ip]

    cmd += snmp_paths

    data = []
    ph = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for label, line in zip(snmp_labels, iter(ph.stdout.readline, "")):
        data.append( int(line) )
    ph.wait()

    return data

if __name__ == "__main__":
    data = get_adsl_data()
    print ":".join(str(x) for x in data)
