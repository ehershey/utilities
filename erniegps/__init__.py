#!/usr/bin/env python
"""
Utilities for gps data
"""

import dateutil.parser
import ggps
import logging
import m26
import math
import pytz

MAX_SPLIT_DEPTH = 30

# How much to try taking off of a track/s beginning and/or end in order to
# coerce it into a negative split
#
PERCENTAGE_MARGIN_SPLIT_ADVANTAGE = 10

logging.basicConfig(level=logging.DEBUG)


class ActivityException(Exception):

    def __init__(self):
        Exception.__init__(self)

    def __init__(self, msg):
        Exception.__init__(self, msg)


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
    """Return an m26.Speed object representing speed over the given trackpoints"""

    if len(trackpoints) < 1:
        return m26.Speed(m26.Distance(0), m26.ElapsedTime(0))

    first_trackpoint = trackpoints[0]
    last_trackpoint = trackpoints[-1]

    # pull time and distance differences between first and last trackpoints
    #
    # 'elapsedtime': '00:55:22', 'runcadencex2': '170', u'time': u'2017-05-23T00:03:28.000Z', 'distancemiles': '6.13382732075'
    first_elapsedtime = first_trackpoint.get('elapsedtime')

    first_etime = m26.ElapsedTime(first_elapsedtime)

    last_elapsedtime = last_trackpoint.get('elapsedtime')

    last_etime = m26.ElapsedTime(last_elapsedtime)

    diff_distance = get_distance_from_trackpoints(trackpoints)
    diff_etime = m26.ElapsedTime(last_etime.secs - first_etime.secs)

    logging.debug("diff_distance: {0}".format(diff_distance))
    logging.debug("diff_etime: {0}".format(diff_etime))

    speed = m26.Speed(diff_distance, diff_etime)
    return speed


def split_trackpoints(trackpoints):
    last_trackpoint = trackpoints[-1]
    first_trackpoint = trackpoints[0]

    diff_distancemiles = get_distance_from_trackpoints(trackpoints).as_miles()
    half_distancemiles = diff_distancemiles / 2
    logging.debug("split_trackpoints: diff_distancemiles: {0}".format(diff_distancemiles))
    logging.debug("split_trackpoints: half_distancemiles: {0}".format(half_distancemiles))

    crossed_half = False
    first_half = []
    last_half = []
    for index in range(0, len(trackpoints)):
        trackpoint = trackpoints[index]
        # distance to this trackpoint from first one
        distance_to_point = get_distance_from_trackpoints(trackpoints[0:index + 1]).as_miles()
        logging.debug("split_trackpoints: distance_to_point: {0}".format(distance_to_point))
        if distance_to_point < half_distancemiles:
            first_half.append(trackpoint)
        else:
            last_half.append(trackpoint)

    return (first_half, last_half)


def format_pace(speed):
    spm = speed.seconds_per_mile()
    mm = int(math.floor(spm / 60.0))
    ss = int(spm - (mm * 60.0))
    return "{0:.0f}:{0:02.0f}".format(mm, ss)


def get_pace(trackpoints):
    return format_pace(get_speed_from_trackpoints(trackpoints))


def read_activity(filename):
    activity = {"filename": filename}
    tcx_handler = ggps.TcxHandler()
    tcx_handler.parse(filename)

    trackpoints = tcx_handler.trackpoints
    activity_type = tcx_handler.activity_type
    notes = tcx_handler.notes
    activity['trackpoints'] = trackpoints
    activity['activity_type'] = activity_type
    activity['notes'] = notes
    activity['verbose_startdate'] = dateutil.parser.parse(trackpoints[0].get('time')).astimezone(pytz.timezone("EST5EDT")).strftime("%Y-%m-%d")
    activity['verbose_starttime'] = dateutil.parser.parse(trackpoints[0].get('time')).astimezone(pytz.timezone("EST5EDT")).strftime("%H:%M")
    activity['starttime'] = dateutil.parser.parse(trackpoints[0].get('time')).astimezone(pytz.timezone("EST5EDT"))
    activity['endtime'] = dateutil.parser.parse(trackpoints[len(trackpoints) - 1].get('time')).astimezone(pytz.timezone("EST5EDT"))
    activity['verbose_duration'] = str(activity['endtime'] - activity['starttime'])
    activity['verbose_distance'] = "{0:.02f} miles".format(get_distance_from_trackpoints(trackpoints).as_miles())
    return activity


def get_is_negative_split(trackpoints):
    """ Look at the given set of trackpoints and return a boolean indicating whether
    the pace of the second half was faster than the pace of the first half. An attempt
    is made to coerce the trackpoints into a negative split by taking up to
    PERCENTAGE_MARGIN_SPLIT_ADVANTAGE percent of the track points off of the list, including
    the start and the end (for warm ups and cool downs).
    """
    (first_half_trackpoints, last_half_trackpoints) = split_trackpoints(trackpoints)
    logging.debug("len(trackpoints): {0}".format(len(trackpoints)))
    logging.debug("len(first_half_trackpoints): {0}".format(len(first_half_trackpoints)))
    logging.debug("len(last_half_trackpoints): {0}".format(len(last_half_trackpoints)))

    logging.debug("get_pace(trackpoints): {0}".format(get_pace(trackpoints)))
    logging.debug("get_pace(first_half_trackpoints): {0}".format(get_pace(first_half_trackpoints)))
    logging.debug("get_pace(last_half_trackpoints): {0}".format(get_pace(last_half_trackpoints)))

    first_half_speed = get_speed_from_trackpoints(first_half_trackpoints).mph()
    last_half_speed = get_speed_from_trackpoints(last_half_trackpoints).mph()

    # logging.debug("first_half_speed:", str(first_half_speed))
    logging.debug("first_half_speed:")
    logging.debug(str(first_half_speed))
    # logging.debug("last_half_speed:", str(last_half_speed))
    logging.debug("last_half_speed:")
    logging.debug(str(last_half_speed))
    if last_half_speed > first_half_speed:
        logging.debug("yes")
        return True
    else:

        # try removing up to PERCENTAGE_MARGIN_SPLIT_ADVANTAGE points off the beginning or end if
        # it changes from a positive split to a negative split
        #

        # May be zero if point count < 10
        #
        max_points_to_trim = len(trackpoints) * PERCENTAGE_MARGIN_SPLIT_ADVANTAGE / 100
        for start_points_to_trim in range(max_points_to_trim + 1):
            for end_points_to_trim in range(max_points_to_trim - start_points_to_trim + 1):

                logging.debug("checking trackpoints[ start_points_to_trim : len(trackpoints) - end_points_to_trim ]")
                logging.debug("(checking trackpoints[ {0} : {1} - {2}]".format(str(start_points_to_trim), str(len(trackpoints)), str(end_points_to_trim)))
                if start_points_to_trim > 0 and end_points_to_trim > 0 and get_is_negative_split(trackpoints[start_points_to_trim: len(trackpoints) - end_points_to_trim]):
                    logging.debug("yes")
                    return True

        # despite all efforts, not negative
        #
        logging.debug("no")
        return False


def process_activity(activity):
    trackpoints = activity['trackpoints']

    if get_is_negative_split(trackpoints):
        activity['is_negative_split'] = True
    else:
        logging.debug("no")
        activity['is_negative_split'] = False

    # Determine how many levels into the last half of the track show
    # negative splits - e.g. is the second half also a negative split
    # when treated as its own track
    negative_split_depth = 0
    negative_split = True
    while negative_split is True and negative_split_depth < MAX_SPLIT_DEPTH:
        logging.debug("")
        logging.debug("negative_split_depth: {0}".format(negative_split_depth))
        if get_is_negative_split(trackpoints):
            negative_split = True
            negative_split_depth += 1
        else:
            negative_split = False
        trackpoints = split_trackpoints(trackpoints)[1]
    activity['negative_split_depth'] = negative_split_depth

    # Trackpoints no longer needed
    #
    del(activity['trackpoints'])

    return activity
