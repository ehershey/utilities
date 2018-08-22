#!/usr/bin/env python
"""
convert a gpx file to geojson
"""

import argparse
import json
import logging
import ggps

if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description='gpx to geojson')
    PARSER.add_argument('--entry-source', help='Entry Source for db entries', required=True)
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    ARGS = PARSER.parse_args()

    if ARGS.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))

    GH = ggps.GpxHandler()

    GH.parse("/dev/stdin")

    logging.debug("read input")

    for trackpoint in GH.trackpoints:
        output_point = {
            "entry_date": {"$date": trackpoint.get('time')},
            "entry_source": ARGS.entry_source,
            "loc": {
                "type": "Point",
                "coordinates": [
                    float(trackpoint.get('longitudedegrees')),
                    float(trackpoint.get('latitudedegrees'))
                    ]
                }
            }
        print json.dumps(output_point)
