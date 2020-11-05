"""
Utilities for gps data
"""

import datetime
import dateutil.parser
import geopy.distance
import ggps
import gpxpy
import json
import logging
import m26
import math
import pint
import pytz
from pytz import reference

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
    simple_activity["distance"] = activity.distance.num
    simple_activity["distance_unit"] = activity.distance.unit.specifier
    simple_activity["start_date"] = activity.start_date
    simple_activity["end_date"] = activity.start_date + activity.elapsed_time
    simple_activity["start_date_local"] = activity.start_date_local
    simple_activity["end_date_local"] = activity.start_date_local + activity.elapsed_time
    simple_activity["moving_time"] = activity.moving_time.seconds
    simple_activity["elapsed_time"] = activity.elapsed_time.seconds

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
    for segment in track.segments:
        if len(segment.points) > 0:
            return segment.points[0]


def get_last_point(track):
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

    if activity_start.tzinfo is None:
        if(track is not None and track_start is not None and
           track_start.tzinfo is not None and
           'start_date' in strava_activity and 'end_date' in strava_activity):
            logging.debug("copying tzinfo from UTC")
            activity_start = strava_activity['start_date'].replace(tzinfo=pytz.utc)
            activity_end = strava_activity['end_date'].replace(tzinfo=pytz.utc)
        else:
            logging.debug("copying tzinfo from pytz.reference")
            activity_start = activity_start.replace(tzinfo=reference.LocalTimezone())
            activity_end = activity_end.replace(tzinfo=reference.LocalTimezone())

    return activity_start, activity_end


def get_normalized_livetrack_start_end(livetrack_session, track, track_start):
    """
    Do everything possible to get livetrack session start and end times with timezones
    """
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
    return session_start, session_end
