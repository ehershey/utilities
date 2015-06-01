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

def adjust_color(color, dim_factor=0.10):
    r, g, b = color
    h, s, v = colorsys.rgb_to_hsv(r / 256.0, g / 256.0, b / 256.0)
    r, g, b = colorsys.hsv_to_rgb(h, s, v * dim_factor)
    return int(r * 256), int(g * 256), int(b * 256)


if __name__ == "__main__":

    bt = connect()

    for color in sys.argv[1:]:
        print("sending color: %s" % color)
        c = color_map[color]
        print("c: ")
        print(c)
        c = adjust_color(c)
        print("c: ")
        print(c)
	r, g, b = c
        bt.sendPixel(r, g, b)
    bt.show()
