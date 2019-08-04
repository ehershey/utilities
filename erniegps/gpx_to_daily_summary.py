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
    "calories_by_type": {
        "Cycling": 500,
        "Running": 123,
        "Walking": 321
    }
    "calories_by_entry_source": {
        "Strava": 313,
        "Arc Export": 100
    }
}
#
convert a gpx file to geojson
"""

import argparse
import datetime
import json
import logging
import os
import sys
import gpxpy
import gpxpy.gpx
import pint
from bson import json_util
import erniegps.calories


from pymongo import MongoClient

def get_db_url():
    if "MONGODB_URI" in os.environ:
        return os.environ["MONGODB_URI"]
    else:
        return "localhost"



STRAVA_DB = "strava"
ACTIVITY_COLLECTION = "activities"


def get_summary_type_from_strava_type(type):
    if type == "Ride":
        summary_type = "cycling"
    elif type == "Run":
        summary_type = "running"
    elif type == "Walk":
        summary_type = "walking"
    elif type == "Hike":
        summary_type = "hiking"
    elif type == "Workout":
        summary_type = "gym"
    else:
        raise Exception("Unrecognized activity type: {type}".format(type=type))
    return summary_type


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
        calories = distance_miles * CALORIES_PER_MILE_BY_ACTIVITY_TYPE[activity_type]
        logging.debug("calories: %s", calories)
        return calories
    raise Exception("Unrecognized activity type: {activity_type}".format(
        activity_type=activity_type))


def process_track(track):
    """ Take gpxpy track object and read summary data from it
    """
    distance = track.get_moving_data().moving_distance
    logging.debug("")
    logging.debug("")
    logging.debug("processing new track")
    logging.debug("distance: %f", distance)
    logging.debug("get_points_no(): %f", track.get_points_no())

    time = track.get_moving_data().moving_time
    start_time = track.get_time_bounds().start_time
    if start_time is None:
        return
    start_date = start_time.date()
    end_time = track.get_time_bounds().end_time
    end_date = end_time.date()

    for strava_activity in STRAVA_ACTIVITIES:
        # Split into tracks that don't overlap with strava
        #
        logging.debug("")
        logging.debug("processing strava activity")

        track_start = start_time
        track_end = end_time
        activity_start = strava_activity['start_date_local']
        try:
            activity_end = strava_activity['end_date_local']
        except KeyError as e:
            logging.error("Can't find end_date_local in activity!")
            logging.error(strava_activity)
            exit()

        logging.debug("track_start: {track_start}".format(track_start=track_start))
        logging.debug("track_end: {track_end}".format(track_end=track_end))
        logging.debug("activity_start: {activity_start}".format(activity_start=activity_start))
        logging.debug("activity_end: {activity_end}".format(activity_end=activity_end))

        # * "track" from ARC
        # * "activity" from Strava
        #
        # All comparisons are inclusive of track start and of end
        # ?? not of track end (activity start $gte track start but activty $lt - >= but <
        #
        # for given combination - possibilities are:
        # 1) Track fully enclosed within activity (track start greater than activity start and
        #    track end less than activity end and end)
        #    * Just return - completely ignore track
        # 2) Activity fully enclosed within track (track start less than activity start and
        #    track end greater than activity end)
        #    * Split track into two - one before activity and one after
        # 3) Track start within activity but end is not
        #    * Shrink track to non-overlapping part - from activity end to track end
        # 4) Track start not within activity but end is
        #    * Shrink track to non-overlapping part - from track start to activity start
        # 5) No overlap (all cases should reduce to this)
        #    * process track raw, or keep looking for overlaps

        # 1) Track enclosed within activity
        if track_start >= activity_start and track_end <= activity_end:
            logging.debug("case 1: returning")
            return None
        # 2) Activity enclosed within track
        elif track_start < activity_start and track_end > activity_end:
            logging.debug("case 2: Splitting into two")
            end_track = track.clone()
            for segment in track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time >= activity_start:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del(segment.points[index_to_delete])
            for segment in end_track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time <= activity_end:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del(segment.points[index_to_delete])

            process_track(track)
            process_track(end_track)
            return None
        elif track_start >= activity_start and track_start <= activity_end and track_end \
                >= activity_end:
            logging.debug("case 3: Shrinking track")
            for segment in track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time <= activity_end:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del(segment.points[index_to_delete])
            process_track(track)
            return None
        elif track_start <= activity_start and track_end >= activity_start and track_end \
                <= activity_end:
            logging.debug("case 4: Shrinking track")
            for segment in track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time >= activity_start:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del(segment.points[index_to_delete])
            process_track(track)
            return None
        else:
            logging.debug("case 5: continuing")

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
    elif start_date in SUMMARIES_BY_DATE:
        summary = SUMMARIES_BY_DATE[start_date]
    else:
        summary = dict({
            "entry_source": ARGS.entry_source,
            "Date": start_time.replace(hour=0, minute=0, second=0),
            "Verbose Date": start_time.strftime("%Y-%m-%d"),
            "GPS Points": 0,
            "Calories": 0,
            "Time": 0,
            "Distance": 0,
            "calories_by_type": {},
            "calories_by_entry_source": {ARGS.entry_source: 0}
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
    calories = compute_activity_calories(
        activity_type=tracktype,
        distance_meters=distance,
        duration_secs=time)
    if key not in summary["calories_by_type"]:
        summary["calories_by_type"][key] = 0
    summary["calories_by_type"][key] += calories
    logging.debug("calories: %d", calories)
    summary["calories_by_entry_source"][ARGS.entry_source] += calories
    time_key = tracktype.capitalize() + " Seconds"
    if time_key not in summary:
        summary[time_key] = time
    else:
        summary[time_key] += time

    summary["Time"] += time
    summary["Distance"] += distance
    summary["Calories"] += calories
    summary["GPS Points"] += track.get_points_no()


if __name__ == '__main__':

    PARSER = argparse.ArgumentParser(description='gpx to daily summary')
    PARSER.add_argument('--entry-source', help='Entry Source for db entries', default="None")
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    PARSER.add_argument('--filename', help='File to read', default=None)
    PARSER.add_argument('--skip-strava', help='Do not merge Strava activities', default=False,
                        action='store_true')
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
    STRAVA_ACTIVITIES = []

    UREG = pint.UnitRegistry()

    # get all strava activities that overlap track dates
    #

    seen_strava_activity_ids = {}
    if not ARGS.skip_strava:
        DB_URL = get_db_url()
        mongoclient = MongoClient(DB_URL)

        database = mongoclient[STRAVA_DB]

        collection = database[ACTIVITY_COLLECTION]

        earliest_start_date = None
        latest_end_date = None
        for track in GPX.tracks:
            start_time = track.get_time_bounds().start_time
            end_time = track.get_time_bounds().end_time
            if start_time is None:
                continue
            start_date = datetime.datetime.combine(start_time.date(), datetime.datetime.min.time())
            end_date = datetime.datetime.combine(end_time.date(), datetime.datetime.min.time())
            if earliest_start_date is None or start_date < earliest_start_date:
                earliest_start_date = start_date
            if latest_end_date is None or end_date > latest_end_date:
                latest_end_date = end_date

        if earliest_start_date is not None and latest_end_date is not None:
            start_date = earliest_start_date
            end_date = latest_end_date + datetime.timedelta(days=1)

            # Build up query for:
            # (start in range) OR (end in range)
            # with "in range" meaning "(is after date) AND (is before date + 1 day)"
            # thus:
            # (start is after date AND start is before date + 1) OR (end is after date AND end is
            # before date + 1)
            #
            # Using the "*_local" fields seems appropriate here since the time portions of the
            # comparison date is gone.
            # This will pick up any activities started or ending in this date according to local
            # time.
            # Maybe it should even be between 4am or some other boundary that would include late
            # night jaunts.
            #
            # TODO: fix gaps in strava tracks with activity in ARC
            # TODO: account for strava activity ending on different day only including calories in
            # start date but
            # subtracting from tracks on both ARC days

            query = {"$or": [
                {"$and": [{"start_date_local": {"$gte": start_date}},
                          {"start_date_local": {"$lt": end_date}}]},
                {"$and": [{"end_date_local": {"$gte": start_date}},
                          {"end_date_local": {"$lt": end_date}}]}
                ]}
            logging.debug("query: {query}".format(query=query))
            cursor = collection.find(query)

            for strava_activity in cursor:
                if strava_activity['strava_id'] not in seen_strava_activity_ids:
                    STRAVA_ACTIVITIES.append(strava_activity)
                    seen_strava_activity_ids[strava_activity['strava_id']] = True

    logging.info("Overlapping strava activity count: {count}".format(count=len(STRAVA_ACTIVITIES)))

    for track in GPX.tracks:
        process_track(track)

    for strava_activity in STRAVA_ACTIVITIES:
        start_date = strava_activity['start_date_local'].date()
        end_date = strava_activity['end_date_local'].date()
        distance = strava_activity['distance']
        elapsed_time = strava_activity['elapsed_time']
        calories = strava_activity['calories']

        if start_date in SUMMARIES_BY_DATE:
            summary = SUMMARIES_BY_DATE[start_date]
        elif end_date in SUMMARIES_BY_DATE:
            summary = SUMMARIES_BY_DATE[end_date]
        else:
            raise Exception("No summaries from ARC data matching start_date ({start_date}) or end_date \
                             ({end_date})".format(start_date=start_date, end_date=end_date))

        if 'calories_by_entry_source' not in summary:
            summary['calories_by_entry_source'] = {}
        if 'Strava' not in summary['calories_by_entry_source']:
            summary['calories_by_entry_source']['Strava'] = 0

        type = get_summary_type_from_strava_type(strava_activity['type'])
        key = type.capitalize()
        if key not in summary:
            summary[key] = strava_activity['distance']
        else:
            summary[key] += strava_activity['distance']
        if 'calories' not in strava_activity or strava_activity['calories'] is None or \
                strava_activity['calories'] == 0:
            calories = compute_activity_calories(
                activity_type=type,
                distance_meters=distance,
                duration_secs=elapsed_time)

        if key not in summary['calories_by_type']:
            summary['calories_by_type'][key] = 0
        summary['calories_by_type'][key] += calories

        time_key = type.capitalize() + " Seconds"
        if time_key not in summary:
            summary[time_key] = elapsed_time
        else:
            summary[time_key] += elapsed_time

        logging.debug("adding {calories} to strava total".format(calories=calories))
        summary['calories_by_entry_source']['Strava'] += calories

        summary['Calories'] += calories

    summaries = SUMMARIES_BY_DATE.values()

    # Unless multiples are explicitly allowed, only print the summary with the most points
    #
    if not ARGS.allow_multiple:
        summaries = sorted(summaries, key=lambda summary: summary["GPS Points"], reverse=True)[0:1]

    for summary in summaries:
        print(json.dumps(summary, default=json_util.default))
