#!/usr/bin/python
"""

Listen for Amazon Dash buttons on the network and send their
presses to opensensors.io

"""

import dash_config

# contains roughly the following:
# macs = {
#     "74:c2:46:xx:xx:xx": "tide",
#     "74:c2:46:xx:xx:xx": "gatorade",
#     "74:c2:46:xx:xx:xx": "smartwater",
#     "74:c2:46:xx:xx:xx": "glad"
#     }

# OPENSENSORSTOPIC = "/users/ehershey/dash/{0}"
# OPENSENSORSDEVICEID = xxxx
# OPENSENSORSUSERNAME = 'ehershey'
# OPENSENSORSPASSWORD = 'xxxxxx'
# OPENSENSORSMESSAGE = "Press"


import subprocess
from scapy.all import sniff, ARP
import logging
import signal
import sys


def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


def arp_display(pkt):
    print "ARP query"
    print "pkt[ARP].op: {0}".format(pkt[ARP].op)
    print "pkt[ARP].psrc: {0}".format(pkt[ARP].psrc)
    print "pkt[ARP].hwsrc: {0}".format(pkt[ARP].hwsrc)
    if pkt[ARP].op == 1:  # who-has (request)
        if pkt[ARP].hwsrc in dash_config.macs:
            print "Recognized button"
            label = dash_config.macs[pkt[ARP].hwsrc]
            print "Label: {0}".format(label)
            command = ["mosquitto_pub", "-h", "opensensors.io",
                       "-t", dash_config.OPENSENSORSTOPIC.format(label),
                       "-m", dash_config.OPENSENSORSMESSAGE,
                       "-i", str(dash_config.OPENSENSORSDEVICEID),
                       "-u", dash_config.OPENSENSORSUSERNAME,
                       "-P", dash_config.OPENSENSORSPASSWORD]
            print(command)
            subprocess.call(command)
        else:
            print "unknown hwsrc"
    else:
        print "unknown op"


while True:
    sniff(prn=arp_display, filter="arp", store=0, count=10)
