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
import geopy.distance
import gpxpy
import gpxpy.gpx
import pint
from bson import json_util
from pymongo import MongoClient
import erniegps.calories
import erniegps
import erniegps.db
import erniegps.private
import pytz
import strava_to_db
import uuid


autoupdate_version = 355

# limits for combining tracks
#
MAX_EMPTY_MINUTES_BETWEEN_COMBINED_TRACKS = 30
# MAX_DISTANCE_METERS_BETWEEN_COMBINED_TRACKS = 50
MAX_DISTANCE_METERS_BETWEEN_COMBINED_TRACKS = 110  # 2020-10-24 split walking unnecessarily in two
# MAX_MPH_TO_ASSUME_WALKING = 4  # 2017-10-31 (subway ride ~10mph?)
# MAX_MPH_TO_ASSUME_WALKING = 5.5  # 2020-10-22 a lot of running in between walking
# 2020-11-21 more running in between walking - 5.5 leads to 5 activities
MAX_MPH_TO_ASSUME_WALKING = 5.85


# limits to include tracks in the end at all
MIN_TRACK_DISTANCE_METERS = 70  # 2020-11-21 tiny little 62 meter track on bedford
MIN_TRACK_DURATION_MINUTES = 1
MIN_TRACK_GPS_POINTS = 21  # 2020-10-17 1:30am and others on same day
MIN_TRACK_MILES_FROM_SKIP_CENTERS = .5

AUTO_ACTIVITY_NAME = "Auto walk upload"
AUTO_ACTIVITY_EXTERNAL_ID_PREFIX = "AWU"


NEW_TRACKS = []
STRAVA_ACTIVITIES = []
LIVETRACK_SESSIONS = []

UREG = pint.UnitRegistry()

SKIP_CENTERS = erniegps.private.get_skip_centers()


def process_track(track):
    """ Take gpxpy track object and read new_track data from it """
    logging.debug("")
    logging.debug("")
    logging.debug("processing new track")
    if track is not None:
        distance = erniegps.get_track_distance(track)

        time = track.get_moving_data().moving_time
        start_time = track.get_time_bounds().start_time
        if start_time is not None:
            start_date = start_time.date()
        end_time = track.get_time_bounds().end_time
        if end_time is not None:
            end_date = end_time.date()
        # Split into tracks that don't overlap with external activities from strava or livetrack
        #
        # gather array of [start, end] tuples from exernal sources
        track_start = start_time
        track_end = end_time
        logging.debug("start_time: %s", start_time)
        logging.debug("end_time: %s", end_time)
        logging.debug("distance: %s", distance)
        logging.debug("track.type: %s", track.type)
        logging.debug("get_points_no(): %f", track.get_points_no())
    else:
        logging.debug("track: None")

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
                        date=None,
                        skip_skip_centers=False):
    """
    Return auto walking tracks that should be saved.
    * By default, tracks are trimmed to not overlap any strava
      activities (in DB) (override with skip_strava_*).
    * By default if a track is only within MIN_TRACK_MILES_FROM_SKIP_CENTERS
      miles of a point in SKIP_CENTERS (home, office, etc). It will be
      skipped (override with skip_skip_centers=true)
    * gpx can be a result from gpxpy.parse()
    * If it's absent, gpx_file is the path to a gpx file to load
    * All strava activities can be skipped
    * Strava activities from this function specifically can be skipped
    """

    if gpx is None:
        # gpx_file can be filehandle or path
        if type(gpx_file) == str:
            gpx_file = open(gpx_file)
        gpx = gpxpy.parse(gpx_file)

    global STRAVA_ACTIVITIES, LIVETRACK_SESSIONS

    STRAVA_ACTIVITIES, LIVETRACK_SESSIONS = erniegps.get_external_activities(
            skip_strava=skip_strava,
            gpx=gpx,
            date=date,
            skip_strava_auto_walking=skip_strava_auto_walking,
            auto_walking_patterns=[AUTO_ACTIVITY_NAME, AUTO_ACTIVITY_EXTERNAL_ID_PREFIX])

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
        this_track_distance = erniegps.get_track_distance(this_track)
        this_track_moving_time = this_track.get_moving_data().moving_time
        logging.debug("this_track_type: %s", this_track_type)
        logging.debug("this_track_start_time: %s", this_track_start_time)
        logging.debug("this_track_end_time: %s", this_track_end_time)
        logging.debug("this_track_distance: %s", this_track_distance)
        if this_track_distance == 0:
            this_track_speed = 0
        else:
            this_track_speed = ((this_track_distance *
                                UREG.meters) / (this_track_moving_time *
                                                UREG.seconds)).to('mph').magnitude
        logging.debug("this_track_speed: %s", this_track_speed)
        if len(new_new_tracks) == 0:
            # Don't start a track until there's a running or walking track
            if this_track_type in ('walking', 'running'):
                logging.debug("starting new track")
                new_new_tracks.append(this_track)
            else:
                logging.debug("ignoring track due to no basis track found yet")
            continue
        if this_track_speed > MAX_MPH_TO_ASSUME_WALKING:
            if this_track_type != 'walking':
                logging.debug("ignoring track due to high speed and not type!=walking")
                continue

        most_recent_track = new_new_tracks[-1]
        most_recent_track_type = most_recent_track.type
        most_recent_track_start_time = most_recent_track.get_time_bounds().start_time
        most_recent_track_end_time = most_recent_track.get_time_bounds().end_time
        most_recent_track_distance = erniegps.get_track_distance(most_recent_track)
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
            logging.debug("ignoring track due to no matching case")

    new_track_length = len(new_new_tracks)
    logging.debug("new_track_length: %s", new_track_length)

    # MIN_TRACK_DISTANCE_METERS = 30
    # MIN_TRACK_DURATION_MINUTES = 1
    # MIN_TRACK_GPS_POINTS = 10
    # MIN_TRACK_MILES_FROM_SKIP_CENTERS = .5
    logging.debug("MIN_TRACK_DISTANCE_METERS: %d", MIN_TRACK_DISTANCE_METERS)
    logging.debug("MIN_TRACK_DURATION_MINUTES: %d", MIN_TRACK_DURATION_MINUTES)
    logging.debug("MIN_TRACK_GPS_POINTS: %d", MIN_TRACK_GPS_POINTS)
    logging.debug("MIN_TRACK_MILES_FROM_SKIP_CENTERS: %f", MIN_TRACK_MILES_FROM_SKIP_CENTERS)

    min_duration = datetime.timedelta(minutes=MIN_TRACK_DURATION_MINUTES)

    logging.debug("eliminating small tracks")

    new_new_new_tracks = []
    for track in new_new_tracks:
        # skip for various reasons
        #
        distance = erniegps.get_track_distance(track)

        logging.debug("distance: %d", distance)
        if distance < MIN_TRACK_DISTANCE_METERS:
            logging.debug("skipping due to distance")
            continue

        start_time = track.get_time_bounds().start_time
        end_time = track.get_time_bounds().end_time
        duration = end_time - start_time

        logging.debug("duration: %s", duration)
        if duration < min_duration:
            logging.debug("skipping due to duration")
            continue

        point_count = track.get_points_no()

        logging.debug("point_count: %d", point_count)
        if point_count < MIN_TRACK_GPS_POINTS:
            logging.debug("skipping due to point_count")
            continue

        # if ALL points are within minimum distance from ANY skip center, skip the whole thing
        checked_distance_count = 0
        found_center_close_to_all_points = False
        if not skip_skip_centers:
            for center in SKIP_CENTERS:
                has_points_outside_center = False
                for point in erniegps.get_all_points(track):
                    distance = erniegps.get_distance(point, center)
                    checked_distance_count = checked_distance_count + 1
                    if distance > MIN_TRACK_MILES_FROM_SKIP_CENTERS:
                        has_points_outside_center = True
                if not has_points_outside_center:
                    found_center_close_to_all_points = True
                    continue
            if found_center_close_to_all_points:
                logging.debug("skipping due to all points being within a skip center")
                logging.debug(f"(checked {checked_distance_count} distances)")
                continue

        new_new_new_tracks.append(track)

    new_new_track_length = len(new_new_new_tracks)
    logging.debug("new_new_track_length: %s", new_new_track_length)

    return new_new_new_tracks


def init():
    NEW_TRACKS.clear()
    STRAVA_ACTIVITIES.clear()
    LIVETRACK_SESSIONS.clear()


def main(gpx_input=None, skip_strava=False, skip_strava_auto_walking=False,
         date=None, skip_strava_upload=False,
         skip_skip_centers=False):

    init()

    """ run as a script """
    combined_tracks = get_combined_tracks(gpx_file=gpx_input,
                                          skip_strava=skip_strava,
                                          skip_strava_auto_walking=skip_strava_auto_walking,
                                          date=date,
                                          skip_skip_centers=skip_skip_centers)

    print(f"Tracks to upload: {len(combined_tracks)}")
    for track in combined_tracks:
        distance_meters = erniegps.get_track_distance(track) * UREG.meters
        distance_miles = distance_meters.to(UREG.miles).magnitude
        print("Track:")
        print(f"{ erniegps.get_first_point(track) } -> { distance_miles:.2f} miles")
        print(f"{ erniegps.get_last_point(track) }")
        gpx = gpxpy.gpx.GPX()
        gpx.simplify()
        gpx.tracks.append(track)
        logging.debug("gpx: %.100s", gpx.to_xml())

        if not skip_strava_upload:
            print("uploading to strava")
            new_uuid = uuid.uuid1()
            external_id = f"{AUTO_ACTIVITY_EXTERNAL_ID_PREFIX}-{new_uuid}"
            uploader = strava_to_db.upload_activity(gpx_xml=gpx.to_xml(),
                                                    external_id=external_id,
                                                    activity_type="walk")
            print("waiting for upload")
            activity = uploader.wait(timeout=30)
            print(f"URL:\nhttps://www.strava.com/activities/{activity.id}")
            # strava_to_db.update_db(activity_id = response.)
            # This shouldn't really be necessary if web hooks are working right.
            # But this can fail; the web hook can fail; they should be idempotent and safe enough
            # to try both
            #
            strava_to_db.update_db(lone_detailed_activity=activity)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='gpx to walk tracks')
    PARSER.add_argument('--debug', help='Display debugging info', action='store_true')
    PARSER.add_argument('--filename', help='File to read', default=None)
    PARSER.add_argument('--date', help='Override date in gpx data (required format: YYYY-MM-DD)',
                        default=None)
    PARSER.add_argument('--skip-strava', help='Do not ignore overlapping Strava activities',
                        default=False, action='store_true')
    PARSER.add_argument('--skip-skip-centers', help='Do not ignore tracks within skip centers',
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

    if args.filename:
        GPX_FILE = open(args.filename)
    else:
        GPX_FILE = sys.stdin

    main(gpx_input=GPX_FILE,
         skip_strava=args.skip_strava,
         skip_strava_auto_walking=args.skip_strava_auto_walking,
         date=args.date,
         skip_strava_upload=args.skip_strava_upload,
         skip_skip_centers=args.skip_skip_centers)
