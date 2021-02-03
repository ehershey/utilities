"""
Utilities for gps data
"""

import datetime
import dateutil.parser
import erniegps
import erniegps.db
import geopy.distance
import ggps
import gpxpy
import json
import logging
import m26
import math
import pint
import polyline
from pymongo import MongoClient
import pytz
from pytz import reference, timezone
from timezonefinder import TimezoneFinder

autoupdate_version = 41

tf = TimezoneFinder()

MAX_SPLIT_DEPTH = 30

# How much to try taking off of a track's beginning and/or end in order to
# coerce it into a negative split
#
PERCENTAGE_MARGIN_SPLIT_ADVANTAGE = 10


class Speed(m26.Speed):
    def __init__(self, d, et):
        m26.Speed.__init__(self, d, et)

    def seconds_per_mile(self):
        if self.etime.hours() == 0:
            return 0.0
        elif self.dist.as_miles() == 0:
            return 0.0
        else:
            return m26.Speed.seconds_per_mile(self)

    def mph(self):
        if self.etime.hours() == 0:
            return 0
        else:
            return m26.Speed.mph(self)


class GpxHandler(ggps.GpxHandler):
    def __init__(self):
        ggps.GpxHandler.__init__(self)
        self.activity_type = None
        self.notes = None

    def endElement(self, tag_name):
        if tag_name == "Notes":
            self.notes = self.curr_text
        ggps.GpxHandler.endElement(self, tag_name)

    def endElement(self, tag_name):
        if tag_name == "type":
            self.activity_type = self.curr_text
        ggps.GpxHandler.endElement(self, tag_name)


class TcxHandler(ggps.TcxHandler):
    def __init__(self):
        ggps.TcxHandler.__init__(self)
        self.activity_type = None
        self.notes = None

    def endElement(self, tag_name):
        if tag_name == "Notes":
            self.notes = self.curr_text
        ggps.TcxHandler.endElement(self, tag_name)

    def startElement(self, tag_name, attrs):
        if tag_name == "Activity" and "Sport" in attrs.keys():
            self.activity_type = attrs.get("Sport")
        ggps.TcxHandler.startElement(self, tag_name, attrs)


def get_distance_from_trackpoints(trackpoints):
    """Return an m26.Distance object representing distance over the given trackpoints"""

    if len(trackpoints) < 1:
        return m26.Distance(0)

    first_trackpoint = trackpoints[0]
    last_trackpoint = trackpoints[-1]

    first_distancemiles = first_trackpoint.get("distancemiles", 0.0)
    last_distancemiles = last_trackpoint.get("distancemiles", 0.0)
    return m26.Distance(float(last_distancemiles) - float(first_distancemiles))


def get_speed_from_trackpoints(trackpoints):
    """Return a Speed object representing speed over the given trackpoints"""

    if len(trackpoints) < 1:
        return Speed(m26.Distance(0), m26.ElapsedTime(0))

    first_trackpoint = trackpoints[0]
    last_trackpoint = trackpoints[-1]

    # pull time and distance differences between first and last trackpoints
    #
    # 'elapsedtime': '00:55:22', 'runcadencex2': '170', u'time': u'2017-05-23T00:03:28.000Z',
    # 'distancemiles': '6.13382732075'
    #
    first_elapsedtime = first_trackpoint.get('elapsedtime')

    first_etime = m26.ElapsedTime(first_elapsedtime)

    last_elapsedtime = last_trackpoint.get('elapsedtime')

    last_etime = m26.ElapsedTime(last_elapsedtime)

    diff_distance = get_distance_from_trackpoints(trackpoints)
    diff_etime = m26.ElapsedTime(last_etime.secs - first_etime.secs)

    logging.debug("diff_distance: %f", diff_distance.as_miles())
    logging.debug("diff_etime: %s", diff_etime)

    speed = Speed(diff_distance, diff_etime)
    return speed


def split_trackpoints(trackpoints):
    """
    Take a trackpoint array; return in two halves
    """
    diff_distancemiles = get_distance_from_trackpoints(trackpoints).as_miles()
    half_distancemiles = diff_distancemiles / 2
    logging.debug("split_trackpoints: diff_distancemiles: %f", diff_distancemiles)
    logging.debug("split_trackpoints: half_distancemiles: %f", half_distancemiles)

    first_half = []
    last_half = []
    for index, trackpoint in enumerate(trackpoints):
        trackpoint = trackpoints[index]
        # distance to this trackpoint from first one
        distance_to_point = get_distance_from_trackpoints(trackpoints[0:index + 1]).as_miles()
        logging.debug("split_trackpoints: distance_to_point: %f", distance_to_point)
        if distance_to_point < half_distancemiles:
            first_half.append(trackpoint)
        else:
            last_half.append(trackpoint)

    return (first_half, last_half)


def format_pace(speed):
    """
    Given a speed, return a human readable string representing pace
    """
    spm = speed.seconds_per_mile()
    minutes = int(math.floor(spm / 60.0))
    seconds = int(spm - (minutes * 60.0))
    return "{0:.0f}:{1:02.0f}".format(minutes, seconds)


def get_pace(trackpoints):
    """
    Return human readable pace for set of trackpoints
    """
    return format_pace(get_speed_from_trackpoints(trackpoints))


def read_activity(filename):
    """
    Read file, return activity object
    """
    activity = {"filename": filename}

    if 'tcx' in filename:
        handler = TcxHandler()
    elif 'gpx' in filename:
        handler = GpxHandler()

    try:
        handler.parse(filename)
    except ValueError as e:
        if str(e) != 'could not convert string to float: ':
            logging.debug("re-raising parse error: {e}".format(e=str(e)))
            raise e
        logging.debug("swallowing valueerror in file parsing")

    trackpoints = handler.trackpoints
    activity_type = handler.activity_type
    notes = handler.notes
    activity['trackpoints'] = trackpoints
    activity['activity_type'] = activity_type
    activity['notes'] = notes

    decorate_activity(activity)
    return activity


def decorate_activity(activity):
    """ Add verbose versions of things and anything else not related to file reading
    """

    trackpoints = activity['trackpoints']
    activity['verbose_startdate'] = dateutil.parser.parse(
        trackpoints[0].get('time')).astimezone(pytz.timezone("EST5EDT")).strftime("%Y-%m-%d")
    activity['verbose_starttime'] = dateutil.parser.parse(
        trackpoints[0].get('time')).astimezone(pytz.timezone("EST5EDT")).strftime("%H:%M")
    activity['starttime'] = dateutil.parser.parse(
        trackpoints[0].get('time')).astimezone(pytz.timezone("EST5EDT"))
    activity['endtime'] = dateutil.parser.parse(
        trackpoints[len(trackpoints) - 1].get('time')).astimezone(pytz.timezone("EST5EDT"))
    activity['verbose_duration'] = str(activity['endtime'] - activity['starttime'])
    activity['verbose_distance'] = "{0:.02f} miles".format(
        get_distance_from_trackpoints(trackpoints).as_miles())
    return activity


def get_is_negative_split(trackpoints, advantage_allowed=True):
    """ Look at the given set of trackpoints and return a boolean indicating whether
    the pace of the second half was faster than the pace of the first half. An attempt
    is made to coerce the trackpoints into a negative split by taking up to
    PERCENTAGE_MARGIN_SPLIT_ADVANTAGE percent of the track points off of the list, including
    the start and the end (for warm ups and cool downs).
    """

    (first_half_trackpoints, last_half_trackpoints) = split_trackpoints(trackpoints)
    logging.debug("advantage_allowed: %d", advantage_allowed)
    logging.debug("len(trackpoints): %d", len(trackpoints))
    logging.debug("len(first_half_trackpoints): %d", len(first_half_trackpoints))
    logging.debug("len(last_half_trackpoints): %d", len(last_half_trackpoints))

    logging.debug("get_pace(trackpoints): %s", get_pace(trackpoints))
    logging.debug("get_pace(first_half_trackpoints): %s", get_pace(first_half_trackpoints))
    logging.debug("get_pace(last_half_trackpoints): %s", get_pace(last_half_trackpoints))

    first_half_speed = get_speed_from_trackpoints(first_half_trackpoints).mph()
    last_half_speed = get_speed_from_trackpoints(last_half_trackpoints).mph()

    logging.debug("first_half_speed: %f", first_half_speed)
    logging.debug("last_half_speed: %f", last_half_speed)

    if last_half_speed > first_half_speed:
        return True
    else:
        if not advantage_allowed:
            return False

        # try removing up to PERCENTAGE_MARGIN_SPLIT_ADVANTAGE points off the beginning or end if
        # it changes from a positive split to a negative split
        #
        for end_percentage in range(1, PERCENTAGE_MARGIN_SPLIT_ADVANTAGE + 1):
            end_points_to_trim = len(trackpoints) * end_percentage // 100
            logging.info("end_percentage: %d", end_percentage)
            logging.info("end_points_to_trim: %d", end_points_to_trim)

            new_last_index = len(trackpoints) - end_points_to_trim
            logging.info("new_last_index: %d", new_last_index)

            if get_is_negative_split(
                    trackpoints[
                        0:new_last_index], False):
                return True

        # despite all efforts, not negative
        #
        return False


def process_strava_activity(activity):
    """
    Convert stravalib activity into a generic dict suitable for mongodb insertion
    """

    simple_activity = {}

    simple_activity["strava_id"] = activity.id
    simple_activity["external_id"] = activity.external_id
    simple_activity["calories"] = activity.calories
    simple_activity["name"] = activity.name
    simple_activity["type"] = activity.type
    simple_activity["map_polyline"] = activity.map.polyline
    simple_activity["distance"] = activity.distance.num
    simple_activity["distance_unit"] = activity.distance.unit.specifier
    simple_activity["start_date"] = activity.start_date
    simple_activity["end_date"] = activity.start_date + activity.elapsed_time
    simple_activity["start_date_local"] = activity.start_date_local
    simple_activity["end_date_local"] = activity.start_date_local + activity.elapsed_time
    simple_activity["moving_time"] = activity.moving_time.seconds
    simple_activity["elapsed_time"] = activity.elapsed_time.seconds

    # get min/max lat/lng from polyline

    # This should return [(40.63179, -8.65708), (40.62855, -8.65693)] in (lat, lon) order.
    coords = polyline.decode(simple_activity["map_polyline"])

    lats = [latlng[0] for latlng in coords]
    lons = [latlng[1] for latlng in coords]
    simple_activity['min_lat'] = min(lats)
    simple_activity['min_lon'] = min(lons)
    simple_activity['max_lat'] = max(lats)
    simple_activity['max_lon'] = max(lons)

    return simple_activity


def process_activity(activity):
    """
    Analyze an activity object and check level of negative splits
    """
    trackpoints = activity['trackpoints']

    # Determine how many levels into the last half of the track show
    # negative splits - e.g. is the second half also a negative split
    # when treated as its own track
    negative_split_depth = 0
    negative_split = True
    while negative_split is True and negative_split_depth < MAX_SPLIT_DEPTH:
        logging.debug("")
        logging.debug("negative_split_depth: %d", negative_split_depth)
        if get_is_negative_split(trackpoints):
            negative_split = True
            negative_split_depth += 1
        else:
            negative_split = False
        trackpoints = split_trackpoints(trackpoints)[1]
    activity['negative_split_depth'] = negative_split_depth

    activity['is_negative_split'] = bool(negative_split_depth >= 1)

    # Trackpoints no longer needed
    #
    del activity["trackpoints"]

    return activity


def get_all_points(track):
    points = []
    for segment in track.segments:
        points.extend(segment.points)
    return points


def get_first_point(track):
    if track is None:
        return None
    for segment in track.segments:
        if len(segment.points) > 0:
            return segment.points[0]


def get_last_point(track):
    if track is None:
        return None
    for segment in reversed(track.segments):
        if len(segment.points) > 0:
            return segment.points[-1]


def shellify(obj):
    """
    convert something like a mongo query python object into something that can be pasted into the
    mongo shell
    """
    logging.debug("type(obj): %s", type(obj))
    logging.debug("str(obj): %s", str(obj))
    logging.debug("repr(obj): %s", repr(obj))
    if isinstance(obj, datetime.time):
        logging.debug("obj is a datetime.time")
        return ISODate(obj)
    elif isinstance(obj, datetime.datetime):
        logging.debug("obj is a datetime.datetime")
        return ISODate(obj)
    else:
        return repr(obj)

    if isinstance(obj, list):
        logging.debug("obj is a list")
        string = " [ "
        for entry in obj:
            if string != " [ ":
                string = string + ", "
            string = string + shellify(entry)
        string = string + " ] "
        return string
    elif isinstance(obj, object):
        logging.debug("obj is a object")
        string = " { "
        for key in obj:
            if isinstance(key, dict):
                raise Exception("key is a dict??: {key}".format(key=key))
            string = string + "\"" + str(key) + "\":"
            string = string + repr(shellify(obj[key]))
        string = string + " } "
        return string
    else:
        logging.debug("obj is a DAMN DEFAULT {type}".format(type=type(obj)))
        return repr(obj)


def queryjsonhandler(obj):
    """
    ~https://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript~
    https://stackoverflow.com/questions/4404742/how-do-i-turn-mongodb-query-into-a-json
    """
    if isinstance(obj, datetime.datetime):
        return ISODate(obj)
    else:
        return json.JSONEncoder().encode(obj)


class ISODate():

    def __init__(self, dt):
        self.orig_str = str(dt.isoformat())
        return None

    def __repr__(self):
        return "ISODate(\"{orig_str}\")".format(orig_str=self.orig_str)

    def toJSON(self):
        return self.__repr__()

    def __str__(self):
        raise Exception("bogus string conversion :( ")


class jsonclass(json.JSONEncoder):
    def __init__(self):
        ggps.GpxHandler.__init__(self)
        logging.debug("holy shit!")


def get_distance(point1, point2):
    """
    return distance in miles as a float between two points of arbitrary types
    points can be:
        1) list: lat, lng
        2) GPXTrackPoint

    The first number is always the latitude and the second is the longitude.
    https://www.thoughtco.com/difference-between-latitude-and-longitude-4070791

    """
    lat1 = None
    lat2 = None
    lon1 = None
    lon2 = None
    if type(point1) == gpxpy.gpx.GPXTrackPoint:
        lat1 = point1.latitude
        lon1 = point1.longitude
    elif type(point1) == list:
        lat1 = point1[0]
        logging.debug("point[1]: %f", point1[1])
        lon1 = point1[1]
    else:
        raise Error("Unsupported point type: ", type(point1))

    if type(point2) == gpxpy.gpx.GPXTrackPoint:
        lat2 = point2.latitude
        lon2 = point2.longitude
    elif type(point2) == list:
        lat2 = point2[0]
        lon2 = point2[1]
    else:
        raise Error("Unsupported point type: ", type(point2))

    return geopy.distance.distance([lat1, lon1], [lat2, lon2]).miles


def get_normalized_strava_start_end(strava_activity, track, track_start):
    """
    Do everything possible to get start and end time with timezones for a strava activity
    """
    activity_start = strava_activity['start_date_local']
    logging.debug(f"activity_start: {activity_start}")
    logging.debug(f"activity_start.tzinfo: {activity_start.tzinfo}")
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
            raise Exception("Can't find end_date_local or elapsed_time in activity!")

    logging.debug(f"activity_end: {activity_end}")
    logging.debug(f"activity_end.tzinfo: {activity_end.tzinfo}")

    if activity_start.tzinfo is None:
        first_point = erniegps.get_first_point(track)
        # use tz-aware dates from strava if possible
        if 'start_date' in strava_activity and 'end_date' in strava_activity:
            logging.debug("setting tzinfo to UTC on non-local strava dates")
            activity_start = pytz.utc.localize(strava_activity['start_date'])
            activity_end = pytz.utc.localize(strava_activity['end_date'])
        elif first_point:
            logging.debug("setting tzinfo based on lat/long of first point in track")
            timezone_name = tf.timezone_at(lng=first_point.longitude, lat=first_point.latitude)
            tz = timezone(timezone_name)
            activity_start = tz.localize(activity_start)
            activity_end = tz.localize(activity_end)
        elif track is not None and track_start is not None and track_start.tzinfo is not None:
            logging.debug("copying tzinfo from track start")
            activity_start = track_start.tzinfo.localize(activity_start)
            activity_end = track_start.tzinfo.localize(activity_end)
        else:
            logging.debug("copying tzinfo from pytz.reference")
            activity_start = reference.LocalTimezone().localize(activity_start)
            activity_end = reference.LocalTimezone().localize(activity_end)

    logging.debug(f"returning normalized start/end")
    logging.debug(f"activity_start: {activity_start}")
    logging.debug(f"activity_start.tzinfo: {activity_start.tzinfo}")
    logging.debug(f"activity_end: {activity_end}")
    logging.debug(f"activity_end.tzinfo: {activity_end.tzinfo}")
    return activity_start, activity_end


# TODO: Don't use local timezone if no track. try harder to use from a waypoint or something
#
def get_normalized_livetrack_start_end(livetrack_session, track, track_start):
    """
    Do everything possible to get livetrack session start and end times with timezones
    """
    trackpoints = livetrack_session['trackPoints']
    logging.info("livetrack trackpoint count: %d", len(trackpoints))
    if len(trackpoints) == 0:
        session_start = dateutil.parser.parse(livetrack_session['start'])
        session_end = dateutil.parser.parse(livetrack_session['end'])
    else:
        first_trackpoint = trackpoints[0]
        last_trackpoint = trackpoints[-1]
        logging.debug("first_trackpoint: %s", first_trackpoint)
        logging.debug("last_trackpoint: %s", last_trackpoint)

        first_datetime = first_trackpoint['dateTime']
        if type(first_datetime) == datetime.datetime:
            session_start = first_datetime
        else:
            session_start = dateutil.parser.parse(first_datetime)

        last_datetime = last_trackpoint['dateTime']
        if type(last_datetime) == datetime.datetime:
            session_end = last_datetime
        else:
            session_end = dateutil.parser.parse(last_datetime)

    logging.debug(f"session_start: {session_start}")
    logging.debug(f"session_start.tzinfo: {session_start.tzinfo}")
    logging.debug(f"session_end: {session_end}")
    logging.debug(f"session_end.tzinfo: {session_end.tzinfo}")
    if session_start.tzinfo is None:
        if track is not None and track_start is not None and track_start.tzinfo is not None:
            logging.debug("copying tzinfo from track start")
            session_start = session_start.replace(tzinfo=track_start.tzinfo)
            session_end = session_end.replace(tzinfo=track_start.tzinfo)
        else:
            logging.debug("copying tzinfo from pytz.reference")
            session_start = session_start.replace(tzinfo=reference.LocalTimezone())
            session_end = session_end.replace(tzinfo=reference.LocalTimezone())
    elif session_start.tzinfo == pytz.utc or session_start.tzinfo == dateutil.tz.tzutc():
        logging.debug("converting tzinfo to pytz.reference")
        session_start = session_start.astimezone(reference.LocalTimezone())
        session_end = session_end.astimezone(reference.LocalTimezone())
    logging.debug(f"returning normalized start/end")
    logging.debug(f"session_start: {session_start}")
    logging.debug(f"session_start.tzinfo: {session_start.tzinfo}")
    logging.debug(f"session_end: {session_end}")
    logging.debug(f"session_end.tzinfo: {session_end.tzinfo}")
    return session_start, session_end


def get_external_activities(skip_strava=False,
                            gpx=None,
                            date=None,
                            skip_strava_auto_walking=False,
                            auto_walking_patterns=[]):
    """
    get all strava and livetrack activities that overlap gpx track dates
    """
    STRAVA_ACTIVITIES = []
    LIVETRACK_SESSIONS = []

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
        if gpx:
            for track in gpx.tracks:
                start_time = track.get_time_bounds().start_time
                end_time = track.get_time_bounds().end_time
                if start_time is None:
                    continue
                start_date = datetime.datetime.combine(start_time.date(),
                                                       datetime.datetime.min.time())
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

        one_day = datetime.timedelta(days=1)
        if earliest_start_date is not None and latest_end_date is not None:
            start_date = earliest_start_date
            end_date = latest_end_date + one_day

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

            # go a day further back because livetrack start/end dates are funky
            #
            query = {"$or": [
                {"$and": [{"start_date_local": {"$gte": start_date - one_day}},
                          {"start_date_local": {"$lt": end_date}}]},
                {"$and": [{"end_date_local": {"$gte": start_date - one_day}},
                          {"end_date_local": {"$lt": end_date}}]}
                ]}
            logging.debug("strava query: %s", erniegps.shellify(query))
            cursor = activity_collection.find(query)

            for strava_activity in cursor:
                start_date_local = strava_activity['start_date_local']
                logging.debug(f"start_date_local: {start_date_local}")
                logging.debug(f"start_date_local.tzinfo: {start_date_local.tzinfo}")
                if strava_activity['strava_id'] not in seen_strava_activity_ids:
                    seen_strava_activity_ids[strava_activity['strava_id']] = True
                    skip_this_one = False
                    for auto_walking_pattern in auto_walking_patterns:
                        if skip_strava_auto_walking and \
                           (('name' in strava_activity and
                            strava_activity['name'] == auto_walking_pattern) or
                            ('external_id' in strava_activity and
                                strava_activity['external_id'] is not None and
                                f"{auto_walking_pattern}-" in strava_activity['external_id'])):
                            skip_this_one = True
                            logging.debug("skipping auto walking track")
                            logging.debug("strava_activity: %s", strava_activity)
                            continue
                    if not skip_this_one:
                        STRAVA_ACTIVITIES.append(strava_activity)

            query = {"$or": [
                {"$and": [{"start": {"$gte": str(start_date)}},
                          {"start": {"$lt": str(end_date)}}]},
                {"$and": [{"end": {"$gte": str(start_date)}},
                          {"end": {"$lt": str(end_date)}}]}
                ]}
            logging.debug("livetrack query: %s", query)
            cursor = session_collection.find(query)

            for livetrack_session in cursor:
                if livetrack_session['sessionId'] not in seen_livetrack_session_ids:
                    if 'trackPoints' not in livetrack_session:
                        livetrack_session['trackPoints'] = []
                    LIVETRACK_SESSIONS.append(livetrack_session)
                    seen_livetrack_session_ids[livetrack_session['sessionId']] = True
    return STRAVA_ACTIVITIES, LIVETRACK_SESSIONS


def get_track_distance(track):
    """Return number of meters representing moving distance of the given track"""
    return track.get_moving_data().moving_distance
