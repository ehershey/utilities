#!/usr/bin/env python3
"""


Take gpx data and generate a daily summary of calories, durations, and distances per ativity type

{
    "Walking": "6.76mi",
    "Cycling": "95.14mi",
    "Running Seconds": 4676.0,
    "Calories": 5402.0,
    "Running": "5.61mi",
    "Date": {"$date": "2017-12-15T00:00:00.000Z"},
    "Walking Seconds": 8909.0,
    "Cycling Seconds": 23204.0,
    "entry_source": "Arc Export"
}
#
convert a gpx file to geojson
"""

import argparse
import datetime
import json
import logging
import sys
import gpxpy
import gpxpy.gpx
import pint
from bson import json_util
import erniegps.calories


def compute_activity_calories(activity_type, duration_secs, distance_meters):
    """
    Return how many calories were burned during the given activity
    """

    if isinstance(distance_meters, UREG.Quantity) and distance_meters.unit == UREG.meter:
        distance_meters = distance_meters / UREG.meter

    # Ultimately, duration should be used to adjust the multiplier for when
    # the activity took so long or was so fast that it's not reasonable to use
    # these numbers as simple deltas from basal caloric burn.

    distance_miles = (distance_meters * UREG.meter).to('miles').magnitude
    logging.debug("duration: %s", datetime.timedelta(seconds=duration_secs))
    logging.debug("distance_miles: %s", distance_miles)
    if activity_type in CALORIES_PER_MILE_BY_ACTIVITY_TYPE:
        return distance_miles * CALORIES_PER_MILE_BY_ACTIVITY_TYPE[activity_type]
    raise Exception("Unrecognized activity type: {activity_type}".format(
        activity_type=activity_type))


def process_track(track):
    """ Take gpxpy track object and read summary data from it
    """
    distance = track.get_moving_data().moving_distance
    logging.debug("distance: %f", distance)
    logging.debug("get_points_no(): %f", track.get_points_no())
    time = track.get_moving_data().moving_time
    start_time = track.get_time_bounds().start_time
    if start_time is None:
        return
    start_date = start_time.date()
    end_time = track.get_time_bounds().end_time
    end_date = end_time.date()
    if start_date != end_date:
        # Split into one track for start_date date and one for everything else
        #
        new_dates_track = track.clone()
        logging.debug("track: {track}".format(track=track))
        logging.debug("new_dates_track: {new_dates_track}".format(new_dates_track=new_dates_track))
        for segment in track.segments:
            indexes_to_delete = []
            for index, point in enumerate(segment.points):
                if point.time.date() != start_date:
                    indexes_to_delete.append(index)

            for index_to_delete in reversed(sorted(indexes_to_delete)):
                del(segment.points[index_to_delete])
        for segment in new_dates_track.segments:
            indexes_to_delete = []
            for index, point in enumerate(segment.points):
                if point.time.date() == start_date:
                    indexes_to_delete.append(index)

            for index_to_delete in reversed(sorted(indexes_to_delete)):
                del(segment.points[index_to_delete])

        process_track(track)
        process_track(new_dates_track)
        return None
    if start_date in SUMMARIES_BY_DATE:
        summary = SUMMARIES_BY_DATE[start_date]
    else:
        summary = dict({
            "entry_source": ARGS.entry_source,
            "Date": start_time.replace(hour=0, minute=0, second=0),
            "Verbose Date": start_time.strftime("%Y-%m-%d"),
            "GPS Points": 0,
            "Calories": 0,
            "Time": 0,
            "Distance": 0
            })
        SUMMARIES_BY_DATE[start_date] = summary
    tracktype = track.type
    if not tracktype:
        tracktype = "none"
    key = tracktype.capitalize()
    if key not in summary:
        summary[key] = distance
    else:
        summary[key] += distance
    key = tracktype.capitalize() + " Seconds"
    if key not in summary:
        summary[key] = time
    else:
        summary[key] += time
    calories = compute_activity_calories(
        activity_type=tracktype,
        distance_meters=distance,
        duration_secs=time)
    logging.debug("calories: %d", calories)
    summary["Time"] += time
    summary["Distance"] += distance
    summary["Calories"] += calories
    summary["GPS Points"] += track.get_points_no()


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description='gpx to daily summary')
    PARSER.add_argument('--entry-source', help='Entry Source for db entries', default="None")
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    PARSER.add_argument('--filename', help='File to read', default=None)
    PARSER.add_argument('--allow-multiple', help='Allow multiple date summaries in output',
                        action='store_true')
    ARGS = PARSER.parse_args()

    if ARGS.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))

    if not ARGS.entry_source:
        logging.warning('No entry source defined. Using "None"')

    CALORIES_PER_MILE_BY_ACTIVITY_TYPE = erniegps.calories.CALORIES_PER_MILE_BY_ACTIVITY_TYPE

    if ARGS.filename:
        GPX_FILE = open(ARGS.filename)
    else:
        GPX_FILE = sys.stdin

    if ARGS.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))
        logging.debug("Debug logging enabled")

    GPX = gpxpy.parse(GPX_FILE)

    logging.debug("read input")

    SUMMARIES_BY_DATE = dict()

    UREG = pint.UnitRegistry()

    for track in GPX.tracks:
        process_track(track)
    # print("time: {time}".format(time=str(datetime.timedelta(seconds=total_secs))))
    # print("total_calories: {total_calories}".format(total_calories=total_calories))

    summaries = SUMMARIES_BY_DATE.values()

    # Unless multiples are explicitly allowed, only print the summary with the most points
    #
    if not ARGS.allow_multiple:
        summaries = sorted(summaries, key=lambda summary: summary["GPS Points"], reverse=True)[0:1]

    for summary in summaries:
        print(json.dumps(summary, default=json_util.default))
