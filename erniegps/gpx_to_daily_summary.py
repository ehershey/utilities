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
import dateutil
import json
import logging
import os
import sys
import gpxpy
import gpxpy.gpx
import pint
from bson import json_util
import erniegps.calories
import erniegps.db
import erniegps
from pytz import reference
import pytz


autoupdate_version = 127


def get_summary_type_from_other_type(other_type):
    """ return type for DB based on type from Strava """
    if other_type == "Ride":
        summary_type = "cycling"
    elif other_type == "CYCLING":
        summary_type = "cycling"
    elif other_type == "Run":
        summary_type = "running"
    elif other_type == "RUNNING":
        summary_type = "running"
    elif other_type == "Walk":
        summary_type = "walking"
    elif other_type == "hiking":
        summary_type = "hiking"
    elif other_type == "HIKING":
        summary_type = "hiking"
    elif other_type == "Hike":
        summary_type = "hiking"
    elif other_type == "Workout":
        summary_type = "gym"
    elif other_type == "WeightTraining":
        summary_type = "gym"
    elif other_type == "Rowing":
        summary_type = "rowing"
    elif other_type == "Swim":
        summary_type = "swimming"
    elif other_type == "Elliptical":
        summary_type = "elliptical"
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


def new_summary(start_time, entry_source):
    """ return empty summary object """
    return dict({
        "entry_source": entry_source,
        "Date": start_time.replace(hour=0, minute=0, second=0),
        "Verbose Date": start_time.strftime("%Y-%m-%d"),
        "GPS Points": 0,
        "Calories": 0,
        "Time": 0,
        "Distance": 0,
        "calories_by_type": {},
        "calories_by_entry_source": {entry_source: 0}
        })


def process_track(track):
    """ Take gpxpy track object and read summary data from it """
    logging.debug("")
    logging.debug("")
    logging.debug("processing new track")
    track_start = None
    if track is not None:
        distance = track.get_moving_data().moving_distance
        logging.debug("distance: %f", distance)
        logging.debug("get_points_no(): %f", track.get_points_no())

        time = track.get_moving_data().moving_time
        start_time = track.get_time_bounds().start_time
        if start_time is not None:
            start_date = start_time.date()
        end_time = track.get_time_bounds().end_time
        if end_time is not None:
            end_date = end_time.date()
        # Split into tracks that don't overlap with external activities from strava or livetrack
        #
        # gather array of [start,end] tuples from exernal sources
        track_start = start_time
        track_end = end_time

    external_activities = []

    for strava_activity in STRAVA_ACTIVITIES:
        logging.debug("")
        logging.debug("processing strava activity")
        logging.debug(f"strava_activity: {str(strava_activity)[:80]}")

        (activity_start, activity_end) = erniegps.get_normalized_strava_start_end(strava_activity,
                                                                                  track,
                                                                                  track_start)

        logging.debug("activity_start: %s", activity_start)
        logging.debug("activity_end: %s", activity_end)
        external_activities.append({"start": activity_start, "end": activity_end,
                                    "type": "strava_activity"})

    for livetrack_session in LIVETRACK_SESSIONS:
        logging.debug("")
        logging.debug("processing livetrack session")
        logging.debug(f"livetrack_session: {str(livetrack_session)[:80]}")

        session_start, session_end = erniegps.get_normalized_livetrack_start_end(livetrack_session,
                                                                                 track,
                                                                                 track_start)

        logging.debug("session_start: %s", session_start)
        logging.debug("session_end: %s", session_end)
        # set data for later summarization
        livetrack_session['ernie:infered_start'] = session_start
        livetrack_session['ernie:infered_end'] = session_end

        found_overlap = False
        for external_activity in external_activities:
            external_activity_start = external_activity['start']
            external_activity_end = external_activity['end']
            # session start within external range
            if session_start >= external_activity_start and session_start <= external_activity_end:
                found_overlap = True
                logging.info("Found overlap with another activity: %s", external_activity)
                break
            # session end within external range
            elif session_end >= external_activity_start and session_end <= external_activity_end:
                found_overlap = True
                logging.info("Found overlap with another activity: %s", external_activity)
                break
            # session fully covering external range
            elif session_start <= external_activity_start and session_end >= external_activity_end:
                found_overlap = True
                logging.info("Found overlap with another activity: %s", external_activity)
                break

        if found_overlap:
            livetrack_session["ernie:invalid"] = True
        else:
            external_activities.append({"start": session_start, "end": session_end,
                                        "type": "livetrack_session"})

    if track is None or start_time is None or end_time is None:
        return
    # only one pass needed because none of these should overlap
    #
    for external_activity in external_activities:

        logging.debug("external_activity: %s", external_activity)

        activity_start = external_activity['start']
        activity_end = external_activity['end']

        logging.debug("track_start: %s", track_start)
        logging.debug("track_end: %s", track_end)
        logging.debug("activity_start: %s", activity_start)
        logging.debug("activity_end: %s", activity_end)

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

        # 1) Track enclosed within activity (or exactly the same)
        if track_start >= activity_start and track_end <= activity_end:
            logging.debug("case 1: returning")
            return None
        # 2) Activity enclosed within track
        elif track_start <= activity_start and track_end >= activity_end:
            logging.debug("case 2: Splitting into two")
            end_track = track.clone()
            for segment in track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time >= activity_start:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del segment.points[index_to_delete]
            for segment in end_track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time <= activity_end:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del segment.points[index_to_delete]

            process_track(track)
            process_track(end_track)
            return None
        elif activity_start < track_start <= activity_end < track_end:
            logging.debug("case 3: Shrinking track")
            for segment in track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time <= activity_end:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del segment.points[index_to_delete]
            process_track(track)
            return None
        elif track_start <= activity_start < track_end <= activity_end:
            logging.debug("case 4: Shrinking track")
            for segment in track.segments:
                indexes_to_delete = []
                for index, point in enumerate(segment.points):
                    if point.time >= activity_start:
                        indexes_to_delete.append(index)

                for index_to_delete in reversed(sorted(indexes_to_delete)):
                    del segment.points[index_to_delete]
            process_track(track)
            return None
        else:
            logging.debug("case 5: continuing")

    if start_date != end_date:
        # Split into one track for start_date date and one for everything else
        #
        new_dates_track = track.clone()
        logging.debug("track: %s", track)
        logging.debug("new_dates_track: %s", new_dates_track)
        for segment in track.segments:
            indexes_to_delete = []
            for index, point in enumerate(segment.points):
                if point.time.date() != start_date:
                    indexes_to_delete.append(index)

            for index_to_delete in reversed(sorted(indexes_to_delete)):
                del segment.points[index_to_delete]
        for segment in new_dates_track.segments:
            indexes_to_delete = []
            for index, point in enumerate(segment.points):
                if point.time.date() == start_date:
                    indexes_to_delete.append(index)
            for index_to_delete in reversed(sorted(indexes_to_delete)):
                del segment.points[index_to_delete]
        process_track(track)
        process_track(new_dates_track)
        return None
    elif start_date in SUMMARIES_BY_DATE:
        summary = SUMMARIES_BY_DATE[start_date]
    else:
        summary = new_summary(start_time, ARGS.entry_source)
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


def main(skip_strava=False, gpx=None, date=None):
    """ run as a script """

    global STRAVA_ACTIVITIES, LIVETRACK_SESSIONS

    # get all strava and livetrack activities that overlap track dates
    #
    STRAVA_ACTIVITIES, LIVETRACK_SESSIONS = erniegps.get_external_activities(
            skip_strava=skip_strava,
            gpx=gpx,
            date=date)

    logging.info("Overlapping strava activity count: %d", len(STRAVA_ACTIVITIES))
    logging.info("Overlapping livetrack session count: %d", len(LIVETRACK_SESSIONS))

    # uses LIVETRACK_SESSIONS and STRAVA_ACTIVITIES
    #
    for track in gpx.tracks:
        process_track(track)

    # this shouldn't necessary but we do depend on stuff in process_track
    if len(gpx.tracks) == 0:
        process_track(None)

    for livetrack_session in LIVETRACK_SESSIONS:
        # logging.debug("livetrack_session: %s", livetrack_session)
        trackpoints = livetrack_session['trackPoints']
        logging.info("livetrack trackpoint count: %d", len(trackpoints))
        if len(trackpoints) == 0:
            continue
        if "ernie:invalid" in livetrack_session:
            if livetrack_session['ernie:invalid']:
                logging.debug("ernie:invalid=true")
                continue

        last_trackpoint = trackpoints[-1]
        logging.debug("last_trackpoint: %s", last_trackpoint)

        last_trackpoint_fitnesspointdata = last_trackpoint['fitnessPointData']

        start_time = livetrack_session["ernie:infered_start"]
        end_time = livetrack_session["ernie:infered_end"]

        logging.debug("start_time: %s", start_time)
        logging.debug("end_time: %s", end_time)

        if not start_time or not end_time:
            logging.fatal("Missing infered start or end time!")
            exit(2)

        start_date = start_time.date()
        end_date = end_time.date()

        distance = last_trackpoint_fitnesspointdata['totalDistanceMeters']

        logging.debug("start_date: %s", start_date)
        logging.debug("end_date: %s", end_date)

        elapsed_time = last_trackpoint_fitnesspointdata['totalDurationSecs']

        entry_source = 'Livetrack'

        # TODO: account for multiple activity types in one track instead of counting entire thing as
        # final one
        #
        activity_type = last_trackpoint_fitnesspointdata['activityType']

        calories = None

        # Invalidate any livetrack sessions that overlap with strava activities
        # This avoids double counting when strava activities get saved but
        # livetracks are still in the DB

        process_non_gpx_data(start_date, end_date, start_time, entry_source, activity_type,
                             elapsed_time, distance, calories, len(trackpoints))

    for strava_activity in STRAVA_ACTIVITIES:
        start_time = strava_activity['start_date_local']
        start_date = start_time.date()
        end_date = strava_activity['end_date_local'].date()
        distance = strava_activity['distance']
        elapsed_time = strava_activity['elapsed_time']
        entry_source = 'Strava'
        activity_type = strava_activity['type']
        if 'calories' in strava_activity:
            calories = strava_activity['calories']
        else:
            calories = None

        process_non_gpx_data(start_date, end_date, start_time, entry_source, activity_type,
                             elapsed_time, distance, calories, 1)

    summaries = SUMMARIES_BY_DATE.values()

    logging.debug("summaries: {summaries}".format(summaries=summaries))
    logging.debug("filtering summaries")

    if ARGS.date:
        summaries = (summary for summary in summaries if summary['Verbose Date'] == ARGS.date)

    # Unless multiples are explicitly allowed, only print the summary with the most points
    #
    if not ARGS.allow_multiple:
        summaries = sorted(summaries, key=lambda summary: summary["GPS Points"], reverse=True)[0:1]

    for summary in summaries:
        print(json.dumps(summary, default=json_util.default))


def process_non_gpx_data(start_date, end_date, start_time, entry_source, activity_type,
                         elapsed_time, distance, calories, num_gps_points):
    """
        handle strava activities or livetrack sessions

        All arguments are required except calories and num_gps_points.
        `calories` can be None or 0 and they'll be auto computed.
        `num_gps_points` can be 1. It will be used to choose when multiple days are
                         considered for inclusion.
    """

    if start_date in SUMMARIES_BY_DATE:
        summary = SUMMARIES_BY_DATE[start_date]
    elif end_date in SUMMARIES_BY_DATE:
        summary = SUMMARIES_BY_DATE[end_date]
    else:
        summary = new_summary(start_time, ARGS.entry_source)
        SUMMARIES_BY_DATE[start_date] = summary

    if 'calories_by_entry_source' not in summary:
        summary['calories_by_entry_source'] = {}
    if entry_source not in summary['calories_by_entry_source']:
        summary['calories_by_entry_source'][entry_source] = 0

    summary_type = get_summary_type_from_other_type(activity_type)
    key = summary_type.capitalize()
    if key not in summary:
        summary[key] = distance
    else:
        summary[key] += distance

    if calories == 0 or calories is None:
        calories = compute_activity_calories(
            activity_type=summary_type,
            distance_meters=distance,
            duration_secs=elapsed_time)

    if key not in summary['calories_by_type']:
        summary['calories_by_type'][key] = 0
    summary['calories_by_type'][key] += calories

    time_key = key + " Seconds"
    if time_key not in summary:
        summary[time_key] = elapsed_time
    else:
        summary[time_key] += elapsed_time

    logging.debug("adding {calories} to total for source: {entry_source}".format(calories=calories,
                  entry_source=entry_source))
    summary['calories_by_entry_source'][entry_source] += calories

    summary['Time'] += elapsed_time
    summary['Distance'] += distance
    summary['Calories'] += calories
    # Account for weird cases of arc data with weird times including strava from weird times
    # TODO use actual gps points form strava
    summary["GPS Points"] += num_gps_points


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='gpx to daily summary')
    PARSER.add_argument('--entry-source', help='Entry Source for db entries', default="None")
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    PARSER.add_argument('--filename', help='File to read', default=None)
    PARSER.add_argument('--date', help='Override date in gpx data (required format: YYYY-MM-DD)',
                        default=None)
    PARSER.add_argument('--skip-strava', help='Do not merge Strava activities', default=False,
                        action='store_true')
    PARSER.add_argument('--allow-multiple', help='Allow multiple date summaries in output',
                        action='store_true')
    ARGS = PARSER.parse_args()

    FORMAT = '%(levelname)s:%(funcName)s:%(lineno)s %(message)s'
    logging.basicConfig(format=FORMAT)

    if ARGS.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))
        logging.debug("Debug logging enabled")

    if not ARGS.entry_source:
        logging.warning('No entry source defined. Using "None"')

    CALORIES_PER_MILE_BY_ACTIVITY_TYPE = erniegps.calories.CALORIES_PER_MILE_BY_ACTIVITY_TYPE

    if ARGS.filename:
        GPX_FILE = open(ARGS.filename)
    else:
        GPX_FILE = sys.stdin

    GPX = gpxpy.parse(GPX_FILE)

    logging.debug("read input")

    SUMMARIES_BY_DATE = dict()
    STRAVA_ACTIVITIES = []
    LIVETRACK_SESSIONS = []

    UREG = pint.UnitRegistry()

    main(skip_strava=ARGS.skip_strava, gpx=GPX, date=ARGS.date)
