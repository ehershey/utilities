"""
Utilities for gps data
"""

import logging
import math
import dateutil.parser
import ggps
import m26
import pytz

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
        if tag_name == 'Notes':
            self.notes = self.curr_text
        ggps.GpxHandler.endElement(self, tag_name)

    def endElement(self, tag_name):
        if tag_name == 'type':
            self.activity_type = self.curr_text
        ggps.GpxHandler.endElement(self, tag_name)


class TcxHandler(ggps.TcxHandler):
    def __init__(self):
        ggps.TcxHandler.__init__(self)
        self.activity_type = None
        self.notes = None

    def endElement(self, tag_name):
        if tag_name == 'Notes':
            self.notes = self.curr_text
        ggps.TcxHandler.endElement(self, tag_name)

    def startElement(self, tag_name, attrs):
        if tag_name == 'Activity' and 'Sport' in attrs.keys():
            self.activity_type = attrs.get('Sport')
        ggps.TcxHandler.startElement(self, tag_name, attrs)


def get_distance_from_trackpoints(trackpoints):
    """Return an m26.Distance object representing distance over the given trackpoints"""

    if len(trackpoints) < 1:
        return m26.Distance(0)

    first_trackpoint = trackpoints[0]
    last_trackpoint = trackpoints[-1]

    first_distancemiles = first_trackpoint.get('distancemiles', 0.0)
    last_distancemiles = last_trackpoint.get('distancemiles', 0.0)
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
    del activity['trackpoints']

    return activity


def get_first_point(track):
    for segment in track.segments:
        if len(segment.points) > 0:
            return segment.points[0]


def get_last_point(track):
    for segment in reversed(track.segments):
        if len(segment.points) > 0:
            return segment.points[-1]
