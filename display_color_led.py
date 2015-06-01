#!/usr/bin/python
#
# Update BlinkyTape LED's on the command line
#
#
import time
import urllib
import json
import tempfile
import sys
import colorsys
import os
import glob

import BlinkyTape

def connect():
    serialPorts = glob.glob("/dev/ttyACM**")

    if not serialPorts:
        sys.exit("Could not locate a BlinkyTape.")

    port = serialPorts[0]

    print "BlinkyTape found at: %s" % port

    bt = BlinkyTape.BlinkyTape(port)
    bt.displayColor(0, 0, 0)
    return bt


color_map = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'blank': (0, 0, 0),
    'white': (255, 255, 255),
}


if __name__ == "__main__":

    bt = connect()

    for color in sys.argv[1:]:
        print("sending color: %s" % color)
        r, g, b = color_map[color]
        bt.sendPixel(r, g, b)
    bt.show()
