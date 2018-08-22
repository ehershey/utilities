#!/usr/bin/env python3
"""
Calculate calories from a gpx file
"""

import datetime
import argparse
import logging
import sys
import gpxpy
import gpxpy.gpx
import pint

# These should probably be based on some time based inputs -
#  - Weight at the time of the activity
#  - Elevation ups and downs
#  - Heart rate, which is mostly just available all the time
#

CALORIES_PER_MILE_BY_ACTIVITY_TYPE = {
        'running': 110,
        'walking': 100,
        'cycling': 40,
        'bus': 0,
        'train': 0,
        'transport': 0,
        'car': 0,
        'stationary': 0,
        'airplane': 0
        }


def compute_activity_calories(activity_type, duration_secs, distance_meters):
    """
    Return how many calories were burned during the given activity
    """

    if type(distance_meters) == UREG.Quantity and distance_meters.unit == UREG.meter:
        distance_meters = distance_meters / UREG.meter

    # Ultimately, duration should be used to adjust the multiplier for when
    # the activity took so long or was so fast that it's not reasonable to use
    # these numbers as simple deltas from basal caloric burn.
    #

    distance_miles = (distance_meters * UREG.meter).to('miles').magnitude
    logging.debug("duration: %s", datetime.timedelta(seconds=duration_secs))
    logging.debug("distance_miles: %s", distance_miles)
    if activity_type in CALORIES_PER_MILE_BY_ACTIVITY_TYPE:
        return distance_miles * CALORIES_PER_MILE_BY_ACTIVITY_TYPE[activity_type]
    else:
        raise Exception("Unrecognized activity type: {activity_type}".format(
            activity_type=activity_type))


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(dest='filename', nargs='?')
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    ARGS = PARSER.parse_args()
    if ARGS.filename:
        GPX_FILE = open(ARGS.filename)
    else:
        GPX_FILE = sys.stdin

    if ARGS.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))
        logging.debug("Debug logging enabled")

    GPX = gpxpy.parse(GPX_FILE)

    DISTANCES = dict()
    TIMES = dict()

    UREG = pint.UnitRegistry()

    for track in GPX.tracks:
        distance = track.get_moving_data().moving_distance
        time = track.get_moving_data().moving_time
        tracktype = track.type
        if not tracktype:
            tracktype = "none"
        if tracktype not in DISTANCES:
            DISTANCES[tracktype] = 0
            TIMES[tracktype] = 0
        DISTANCES[tracktype] += distance
        TIMES[tracktype] += time

    total_calories = 0
    total_secs = 0
    for tracktype in DISTANCES:
        logging.debug("tracktype: %s", tracktype)
        distance = DISTANCES[tracktype]
        time_secs = TIMES[tracktype]
        total_secs += time_secs
        calories = compute_activity_calories(
            activity_type=tracktype,
            distance_meters=distance,
            duration_secs=time_secs)
        total_calories += calories

        logging.debug("calories: {calories}".format(calories=calories))
    print("time: {time}".format(time=str(datetime.timedelta(seconds=total_secs))))
    print("total_calories: {total_calories}".format(total_calories=total_calories))
