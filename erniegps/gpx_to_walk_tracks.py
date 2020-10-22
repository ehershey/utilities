#!/usr/bin/env python3
"""

Take gpx data and generate walking tracks that don't overlap with strava activities or active
livetracks.

"""
import cProfile
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
from pymongo import MongoClient
import erniegps.calories
import erniegps
import erniegps.db
from pytz import reference
import strava_to_db


autoupdate_version = 201

# limits for combining tracks
#
MAX_EMPTY_MINUTES_BETWEEN_COMBINED_TRACKS = 30
MAX_DISTANCE_METERS_BETWEEN_COMBINED_TRACKS = 50


# limits to include tracks in the end at all
MIN_TRACK_DISTANCE_METERS = 30
MIN_TRACK_DURATION_MINUTES = 1
MIN_TRACK_GPS_POINTS = 21  # 2020-10-17 1:30am and others on same day

AUTO_ACTIVITY_NAME = "Auto walk upload"


NEW_TRACKS = []
STRAVA_ACTIVITIES = []
LIVETRACK_SESSIONS = []


def process_track(track):
    """ Take gpxpy track object and read new_track data from it """
    logging.debug("")
    logging.debug("")
    logging.debug("processing new track")
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
        logging.debug("strava_activity: %s", strava_activity)

        activity_start = strava_activity['start_date_local']
        try:
            activity_end = strava_activity['end_date_local']
        except KeyError:
            if 'elapsed_time' in strava_activity:
                activity_end = activity_start + \
                        datetime.timedelta(seconds=strava_activity['elapsed_time'])
                strava_activity['end_date_local'] = activity_end
            else:
                logging.error("Can't find end_date_local or elapsed_time in activity!")
                logging.error(strava_activity)
                exit()

        if activity_start.tzinfo is None:
            if track is not None and track_start is not None and track_start.tzinfo is not None:
                logging.debug("copying tzinfo from track start")
                activity_start = strava_activity['start_date'].replace(tzinfo=track_start.tzinfo)
                activity_end = strava_activity['end_date'].replace(tzinfo=track_end.tzinfo)
            else:
                logging.debug("copying tzinfo from pytz.reference")
                activity_start = activity_start.replace(tzinfo=reference.LocalTimezone())
                activity_end = activity_end.replace(tzinfo=reference.LocalTimezone())

        logging.debug("activity_start: %s", activity_start)
        logging.debug("activity_end: %s", activity_end)
        external_activities.append({"start": activity_start, "end": activity_end,
                                    "type": "strava_activity"})

    for livetrack_session in LIVETRACK_SESSIONS:
        logging.debug("")
        logging.debug("processing livetrack session")
        logging.debug("livetrack_session: %.80s", livetrack_session)
        if 'trackPoints' in livetrack_session:
            trackpoints = livetrack_session['trackPoints']
        else:
            trackpoints = []
        logging.info("livetrack trackpoint count: %d", len(trackpoints))
        if len(trackpoints) == 0:
            session_start = dateutil.parser.parse(livetrack_session['start'])
            session_end = dateutil.parser.parse(livetrack_session['end'])
        else:
            first_trackpoint = trackpoints[0]
            last_trackpoint = trackpoints[-1]
            logging.debug("first_trackpoint: %s", first_trackpoint)
            logging.debug("last_trackpoint: %s", last_trackpoint)

            session_start = dateutil.parser.parse(first_trackpoint['dateTime'])
            session_end = dateutil.parser.parse(last_trackpoint['dateTime'])

        if session_start.tzinfo is None:
            if track is not None and track_start is not None and track_start.tzinfo is not None:
                logging.debug("copying tzinfo from track start")
                session_start = session_start.replace(tzinfo=track_start.tzinfo)
                session_end = session_end.replace(tzinfo=track_start.tzinfo)
            else:
                logging.debug("copying tzinfo from pytz.reference")
                session_start = session_start.replace(tzinfo=reference.LocalTimezone())
                session_end = session_end.replace(tzinfo=reference.LocalTimezone())

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

        # track: 17:42:30 - 18:03:27
        # activity: 17:42:30 - 18:03:24

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
    logging.debug("Got non-overlapping track:")
    logging.debug("start_time: %s", start_time)
    logging.debug("end_time: %s", end_time)
    logging.debug("distance: %s", distance)
    logging.debug("track.type: %s", track.type)
    NEW_TRACKS.append(track)


def get_combined_tracks(gpx=None, gpx_file=None, skip_strava=False, skip_strava_auto_walking=False,
                        date=None):
    # get all strava and livetrack activities that overlap track dates
    #

    if gpx is None and type(gpx_file) == str:
        gpx = gpxpy.parse(open(gpx_file))

    seen_strava_activity_ids = {}
    seen_livetrack_session_ids = {}
    if not skip_strava:
        db_url = erniegps.db.get_db_url()
        mongoclient = MongoClient(db_url)

        strava_db = mongoclient[erniegps.db.STRAVA_DB]
        livetrack_db = mongoclient[erniegps.db.LIVETRACK_DB]

        activity_collection = strava_db[erniegps.db.ACTIVITY_COLLECTION]
        session_collection = livetrack_db[erniegps.db.SESSION_COLLECTION]

        earliest_start_date = None
        latest_end_date = None
        for track in gpx.tracks:
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
        for waypoint in gpx.waypoints:
            waypoint_timestamp_date = datetime.datetime.combine(waypoint.time,
                                                                datetime.datetime.min.time())
            if earliest_start_date is None or waypoint_timestamp_date < earliest_start_date:
                earliest_start_date = waypoint_timestamp_date
            if latest_end_date is None or waypoint_timestamp_date > latest_end_date:
                latest_end_date = waypoint_timestamp_date
        if date:
            date_arg_obj = datetime.datetime.strptime(date, '%Y-%m-%d')

            if earliest_start_date is None or date_arg_obj < earliest_start_date:
                earliest_start_date = date_arg_obj
            if latest_end_date is None or date_arg_obj > latest_end_date:
                latest_end_date = date_arg_obj

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
            # start date but subtracting from tracks on both ARC days
            # TODO: Make sure starting an activity on one day and completing it the next day is
            # fully supported (unit tests?)

            # for gaps - idea to split activity into multiple based on large gaps
            # with activity gpx -
            # split_activities = []
            # current_activity = new_activity()
            # last_point = None
            # # limits
            # MIN_POINT_SPEED_TO_SPLIT_MPH = 50 # too fast to go on bike
            # MIN_POINT_DISTANCE_TO_SPLIT_METERS = 80 # short city block
            # MIN_POINT_TIME_TO_SPLIT_SECONDS = 60 # there should be a point tracked per minute
            # for point in activity.trackpoints:
            #    split = False
            #    if last_point is not None:
            #       elapsed = point.timestamp - last_point.timestamp
            #       if elapsed > MIN_POINT_TIME_TO_SPLIT_SECONDS:
            #           split = True
            #       else:
            #           distance = distance(point, last_point)
            #           if distance > MIN_POINT_DISTANCE_TO_SPLIT_METERS:
            #             split = True
            #           else:
            #               speed = ( distance * MILES_PER_METER ) / elapsed * HOURS_PER_SECOND
            #               if speed > MIN_POINT_SPEED_TO_SPLIT_MPH:
            #                   split = True
            #    last_point = point
            #    if split == True:
            #       split_activities.append(current_activity)
            #       current_activity = new_activity()
            #
            #    current_activity.append(point)
            #

            query = {"$or": [
                {"$and": [{"start_date_local": {"$gte": start_date}},
                          {"start_date_local": {"$lt": end_date}}]},
                {"$and": [{"end_date_local": {"$gte": start_date}},
                          {"end_date_local": {"$lt": end_date}}]}
                ]}
            logging.debug("query: %s", json.dumps(query, default=erniegps.queryjsonhandler))
            cursor = activity_collection.find(query)

            for strava_activity in cursor:
                if strava_activity['strava_id'] not in seen_strava_activity_ids and \
                        ((not skip_strava_auto_walking) or
                         strava_activity['name'] != AUTO_ACTIVITY_NAME):
                    STRAVA_ACTIVITIES.append(strava_activity)
                    seen_strava_activity_ids[strava_activity['strava_id']] = True

            query = {"$or": [
                {"$and": [{"start": {"$gte": str(start_date)}},
                          {"start": {"$lt": str(end_date)}}]},
                {"$and": [{"end": {"$gte": str(start_date)}},
                          {"end": {"$lt": str(end_date)}}]}
                ]}
            logging.debug("query: %s", json.dumps(query, default=erniegps.queryjsonhandler))
            cursor = session_collection.find(query)

            for livetrack_session in cursor:
                if livetrack_session['sessionId'] not in seen_livetrack_session_ids:
                    LIVETRACK_SESSIONS.append(livetrack_session)
                    seen_livetrack_session_ids[livetrack_session['sessionId']] = True

    logging.info("Overlapping strava activity count: %d", len(STRAVA_ACTIVITIES))
    logging.info("Overlapping livetrack session count: %d", len(LIVETRACK_SESSIONS))

    # uses LIVETRACK_SESSIONS and STRAVA_ACTIVITIES
    #
    for track in gpx.tracks:
        process_track(track)

    new_tracks = NEW_TRACKS

    logging.debug("total non-overlapping tracks to consider: %d", len(new_tracks))
    logging.debug("combining tracks")

    if date:
        date_arg_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        logging.debug("date_arg_obj: %s", date_arg_obj)
        new_tracks = list(new_track for new_track in new_tracks if
                          new_track.get_time_bounds().start_time.date() == date_arg_obj or
                          new_track.get_time_bounds().end_time.date() == date_arg_obj)

    max_empty_delta = datetime.timedelta(
            minutes=MAX_EMPTY_MINUTES_BETWEEN_COMBINED_TRACKS)
    # Try really hard to reduce to single long walking tracks
    # MAX_EMPTY_MINUTES_BETWEEN_COMBINED_TRACKS = 30
    new_new_tracks = []
    for index in range(len(new_tracks)):
        logging.debug("examining next pre-combined track")
        logging.debug("index: %d", index)
        this_track = new_tracks[index]
        this_track_type = this_track.type
        this_track_start_time = this_track.get_time_bounds().start_time
        this_track_end_time = this_track.get_time_bounds().end_time
        this_track_distance = this_track.get_moving_data().moving_distance
        logging.debug("this_track_type: %s", this_track_type)
        logging.debug("this_track_start_time: %s", this_track_start_time)
        logging.debug("this_track_end_time: %s", this_track_end_time)
        logging.debug("this_track_distance: %s", this_track_distance)
        if len(new_new_tracks) == 0:
            # Don't start a track until there's a running or walking track
            if this_track_type in ('walking', 'running'):
                logging.debug("starting new track")
                new_new_tracks.append(this_track)
            continue
        most_recent_track = new_new_tracks[-1]
        most_recent_track_type = most_recent_track.type
        most_recent_track_start_time = most_recent_track.get_time_bounds().start_time
        most_recent_track_end_time = most_recent_track.get_time_bounds().end_time
        most_recent_track_distance = most_recent_track.get_moving_data().moving_distance
        logging.debug("most_recent_track_type: %s", most_recent_track_type)
        logging.debug("most_recent_track_start_time: %s", most_recent_track_start_time)
        logging.debug("most_recent_track_end_time: %s", most_recent_track_end_time)
        logging.debug("most_recent_track_distance: %s", most_recent_track_distance)

        this_track_start_point = erniegps.get_first_point(this_track)
        most_recent_track_end_point = erniegps.get_last_point(most_recent_track)

        logging.debug("this_track_start_point: %s", this_track_start_point)
        logging.debug("most_recent_track_end_point: %s", most_recent_track_end_point)

        distance_from_last_track = this_track_start_point.distance_3d(most_recent_track_end_point)
        logging.debug("distance_from_last_track: %s", distance_from_last_track)

        time_diff = this_track_start_time - most_recent_track_end_time

        logging.debug("time_diff: %s", time_diff)

        logging.debug("Checking whether track can be absorbed.")
        logging.debug("time_diff < max_empty_delta and")
        logging.debug("distance_from_last_track < MAX_DISTANCE_METERS_BETWEEN_COMBINED_TRACKS")
        logging.debug("%s < %s and", time_diff, max_empty_delta)
        logging.debug("%f < %f", distance_from_last_track,
                      MAX_DISTANCE_METERS_BETWEEN_COMBINED_TRACKS)
        if time_diff < max_empty_delta and \
           distance_from_last_track < MAX_DISTANCE_METERS_BETWEEN_COMBINED_TRACKS:
            logging.debug("absorbing new track")
            for segment in this_track.segments:
                most_recent_track.segments.append(segment)
        elif this_track_type in ('walking', 'running'):
            logging.debug("starting new track")
            new_new_tracks.append(this_track)
        else:
            logging.debug("ignoring track")

    new_track_length = len(new_new_tracks)
    logging.warning("new_track_length: %s", new_track_length)

    # MIN_TRACK_DISTANCE_METERS = 30
    # MIN_TRACK_DURATION_MINUTES = 1
    # MIN_TRACK_GPS_POINTS = 10
    logging.debug("MIN_TRACK_DISTANCE_METERS: %d", MIN_TRACK_DISTANCE_METERS)
    logging.debug("MIN_TRACK_DURATION_MINUTES: %d", MIN_TRACK_DURATION_MINUTES)
    logging.debug("MIN_TRACK_GPS_POINTS: %d", MIN_TRACK_GPS_POINTS)

    min_duration = datetime.timedelta(minutes=MIN_TRACK_DURATION_MINUTES)

    logging.debug("eliminating small tracks")

    new_new_new_tracks = []
    for track in new_new_tracks:
        # skip if not big enough
        #
        distance = track.get_moving_data().moving_distance
        start_time = track.get_time_bounds().start_time
        end_time = track.get_time_bounds().end_time
        duration = end_time - start_time
        point_count = track.get_points_no()

        logging.debug("distance: %d", distance)
        if distance < MIN_TRACK_DISTANCE_METERS:
            logging.debug("skipping due to distance")
            continue

        logging.debug("duration: %s", duration)
        if duration < min_duration:
            logging.debug("skipping due to duration")
            continue

        logging.debug("point_count: %d", point_count)
        if point_count < MIN_TRACK_GPS_POINTS:
            logging.debug("skipping due to point_count")
            continue
        new_new_new_tracks.append(track)

    new_new_track_length = len(new_new_new_tracks)
    logging.warning("new_new_track_length: %s", new_new_track_length)

    return new_new_new_tracks


def init():
    NEW_TRACKS = []
    STRAVA_ACTIVITIES = []
    LIVETRACK_SESSIONS = []


def main(gpx_input=None, skip_strava=False, skip_strava_auto_walking=False,
         date=None, skip_strava_upload=False):

    init()
    gpx = gpxpy.parse(gpx_input)

    logging.debug("read input")

    """ run as a script """
    for track in get_combined_tracks(gpx=gpx,
                                     skip_strava=skip_strava,
                                     skip_strava_auto_walking=skip_strava_auto_walking,
                                     date=date):
        gpx = gpxpy.gpx.GPX()
        gpx.simplify()
        gpx.tracks.append(track)
        logging.debug("gpx: %s", gpx.to_xml())
        if not skip_strava_upload:
            print("uploading to strava")
            uploader = strava_to_db.upload_activity(gpx_xml=gpx.to_xml(),
                                                    name=AUTO_ACTIVITY_NAME,
                                                    activity_type="walk")
            print("waiting for upload")
            activity = uploader.wait(timeout=30)
            # strava_to_db.update_db(activity_id = response.)
            strava_to_db.update_db(lone_detailed_activity=activity)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='gpx to walk tracks')
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    PARSER.add_argument('--filename', help='File to read', default=None)
    PARSER.add_argument('--date', help='Override date in gpx data (required format: YYYY-MM-DD)',
                        default=None)
    PARSER.add_argument('--skip-strava', help='Do not ignore overlapping Strava activities',
                        default=False, action='store_true')
    PARSER.add_argument('--skip-strava-auto-walking',
                        help="""
                        Do not ignore overlapping Strava activities (only auto walking tracks)
                        """,
                        default=False, action='store_true')
    PARSER.add_argument('--skip-strava-upload', help='Do not upload to Strava',
                        default=False, action='store_true')
    args = PARSER.parse_args()

    FORMAT = '%(levelname)s:%(funcName)s:%(lineno)s %(message)s'
    logging.basicConfig(format=FORMAT)

    if args.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))
        logging.debug("Debug logging enabled")

    CALORIES_PER_MILE_BY_ACTIVITY_TYPE = erniegps.calories.CALORIES_PER_MILE_BY_ACTIVITY_TYPE

    if args.filename:
        GPX_FILE = open(args.filename)
    else:
        GPX_FILE = sys.stdin

    main(gpx_input=GPX_FILE,
         skip_strava=args.skip_strava,
         skip_strava_auto_walking=args.skip_strava_auto_walking,
         date=args.date,
         skip_strava_upload=args.skip_strava_upload)
