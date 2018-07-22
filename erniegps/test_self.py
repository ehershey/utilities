#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test erniegps module
"""

import datetime
import logging
import os
import pytz
import erniegps
import m26


def test_zero_speed():
    """
    Test a few weird combinations of:

    Arbitrary distance
    No distance
    Same distance
    Arbitrary elapsed time
    No elapsed time
    Same elapsed time
    """
    """
    Point 1 distance: arbitrary
    Point 1 elapsed time: arbitrary
    Point 2 distance: arbitrary
    Point 2 elapsed time: same
    """
    point1 = {"distancemiles": 50, "elapsedtime": "00:10:00"}
    point2 = {"distancemiles": 60, "elapsedtime": "00:10:00"}
    speed = erniegps.get_speed_from_trackpoints([point1, point2])
    assert speed.mph() == 0
    assert speed.seconds_per_mile() == 0

    assert erniegps.get_speed_from_trackpoints([{
        "distancemiles": 50
    }]).seconds_per_mile() == 0
    assert erniegps.get_speed_from_trackpoints([{}]).mph() == 0
    assert erniegps.get_speed_from_trackpoints([{}]).seconds_per_mile() == 0
    assert erniegps.get_speed_from_trackpoints([]).mph() == 0
    assert erniegps.get_speed_from_trackpoints([]).seconds_per_mile() == 0


def test_zero_distance():
    """
    Ensure zero distances come back as zero distances
    """
    assert erniegps.get_distance_from_trackpoints([{
        "distancemiles": 50
    }]).as_miles() == m26.Distance(0).as_miles()
    assert erniegps.get_distance_from_trackpoints(
        [{}]).as_miles() == m26.Distance(0).as_miles()
    assert erniegps.get_distance_from_trackpoints(
        [{}, {}]).as_miles() == m26.Distance(0).as_miles()
    assert erniegps.get_distance_from_trackpoints(
        []).as_miles() == m26.Distance(0).as_miles()


def test_double_read_activity():
    """
    Make sure reading the same activity file twice works
    """
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(
            os.environ['HOME']))
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(
            os.environ['HOME']))
    trackpoints = activity['trackpoints']
    assert len(trackpoints) == 8


def test_trackpoint_split():
    """ Test simple split """
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(
            os.environ['HOME']))
    trackpoints = activity['trackpoints']
    (first_half_trackpoints,
     last_half_trackpoints) = erniegps.split_trackpoints(trackpoints)
    assert len(first_half_trackpoints) == 2
    assert len(last_half_trackpoints) == 6


def test_no_negative_split():
    """ Test simple track without negative split """
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(
            os.environ['HOME']))
    activity = erniegps.process_activity(activity)
    assert activity.get('is_negative_split') is False
    assert activity.get('negative_split_depth') == 0


def test_empty_distance():
    """
    This track has a trackpoint with no distance that will break an unpatched
    ggps module
    """
    erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2011-02-03_Running.tcx'.format(
            os.environ['HOME']))


def test_get_activity_type():
    """ Patched ggps supports activity_type """
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2017-05-27_New York Running_Running.tcx'.
        format(os.environ['HOME']))
    assert activity['activity_type'] == "Running"
    assert activity['notes'] == "New York Running"


def test_has_verbose_starttime():
    """ Make sure verbose start time gets field added """
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2017-05-27_New York Running_Running.tcx'.
        format(os.environ['HOME']))
    assert isinstance(activity['verbose_starttime'], str)
    assert activity['verbose_starttime'] == '19:03'


def test_has_verbose_distance():
    """ Make sure verbose distance field added """
    activity = erniegps.read_activity(
        '{0}/Dropbox/Apps/tapiriik/2017-05-27_New York Running_Running.tcx'.
        format(os.environ['HOME']))
    assert isinstance(activity['verbose_distance'], str)
    assert activity['verbose_distance'] == '10.13 miles'


def test_handle_unicode_notes_char():
    """ Handle unicode characters properly """
    erniegps.read_activity(
        u'{0}/Dropbox/Apps/tapiriik/2016-06-01_Słomczyn Running_Running.tcx'.
        format(os.environ['HOME']))


def test_fake_track():
    """
    Verify creating a simple track from scratch returns the expected results.

    This is mainly useful for differentiating between problems with basic
    tracks/analysis and more complicated track building/analysis in other tests
    """

    # Constant speed
    trackpoints = []
    for i in range(1, 100):
        point = {"distancemiles": i * 10, "elapsedtime": "{0}:00:00".format(i)}
        trackpoints.append(point)

    speed = erniegps.get_speed_from_trackpoints(trackpoints)

    assert speed.mph() == 10.0
    assert speed.seconds_per_mile() == 360.0

    is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert not is_negative_split


def test_end_negative_split():
    """ Test negative split with one fast point at the end """

    # how many points to use
    #
    point_count = 100

    trackpoints = []
    starttime = datetime.datetime.now(pytz.timezone('US/Eastern'))
    for i in range(0, point_count):
        point = {
            "distancemiles": i * 10,
            "elapsedtime": "{0}:00:00".format(i),
            "time": str(starttime + datetime.timedelta(hours=i))
        }
        trackpoints.append(point)

    # Add one point with the same distance as between each previous point
    # and only taking 30 minutes instead of an hour
    #
    endtime = starttime + datetime.timedelta(hours=point_count - 1, minutes=30)
    trackpoints.append({
        "distancemiles": point_count * 10,
        "elapsedtime": "{0}:30:00".format(point_count - 1),
        "time": str(endtime)
    })

    speed = erniegps.get_speed_from_trackpoints(trackpoints)

    assert speed.mph() > 10.0
    assert speed.seconds_per_mile() < 360.0

    is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert is_negative_split

    activity = {
        "trackpoints": trackpoints,
        "activity_type": "running",
        "notes": "Test activity created in code",
        "starttime": str(starttime),
        "endtime": str(endtime)
        }
    erniegps.decorate_activity(activity)
    erniegps.process_activity(activity)

    negative_split_depth = activity['negative_split_depth']
    assert negative_split_depth >= 2


def test_start_negative_split():
    """ Simple negative split with one slow point at the start """

    # how many points to use
    #
    point_count = 100

    trackpoints = []
    starttime = datetime.datetime.now(pytz.timezone('US/Eastern'))
    for i in range(0, point_count):
        # constant distance per point but add one hour to the overall track
        point = {
            "distancemiles": i * 10,
            "elapsedtime": "{0}:00:00".format(i + 1),
            "time": str(starttime + datetime.timedelta(hours=i + 1))
        }
        trackpoints.append(point)

    # Zero out first point so the second one is two hours later
    #
    endtime = trackpoints[-1]['time']

    trackpoints[0]["elapsedtime"] = "00:00:00"
    trackpoints[0]["time"] = str(starttime)

    speed = erniegps.get_speed_from_trackpoints(trackpoints)

    assert speed.mph() < 10.0
    assert speed.seconds_per_mile() > 360.0

    is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert is_negative_split

    activity = {
        "trackpoints": trackpoints,
        "activity_type": "running",
        "notes": "Test activity created in code",
        "starttime": str(starttime),
        "endtime": str(endtime)
        }
    erniegps.decorate_activity(activity)
    erniegps.process_activity(activity)

    negative_split_depth = activity['negative_split_depth']
    assert negative_split_depth == 1


def test_advantage_split_slow_end(caplog):
    """
    Test detecting a negative split when slow points are at the back of a track

    Constant track base + one fast point + one slow point

    """
    # how many points to use
    #
    point_count = 100

    trackpoints = []
    starttime = datetime.datetime.now(pytz.timezone('US/Eastern'))
    for i in range(0, point_count):
        point = {
            "distancemiles": i * 10,
            "elapsedtime": "{0}:00:00".format(i),
            "time": str(starttime + datetime.timedelta(hours=i))
        }
        trackpoints.append(point)

    # Add one point with the same distance as between each previous point
    # and only taking 45 minutes instead of an hour
    #
    trackpoints.append({
        "distancemiles": point_count * 10,
        "elapsedtime": "{0}:45:00".format(point_count - 1),
        "time": str(starttime + datetime.timedelta(hours=point_count - 1, minutes=45))
    })

    simple_negative_split_speed = erniegps.get_speed_from_trackpoints(trackpoints)

    simple_is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert simple_is_negative_split

    # Add one point with the same distance as between each previous point
    # and taking two hours instead of one
    #
    endtime = starttime + datetime.timedelta(hours=point_count + 1, minutes=45)
    trackpoints.append({
        "distancemiles": (point_count + 1) * 10,
        "elapsedtime": "{0}:45:00".format(point_count + 1),
        "time": str(endtime)
    })

    advantage_negative_split_speed = erniegps.get_speed_from_trackpoints(trackpoints)

    assert simple_negative_split_speed.mph() > advantage_negative_split_speed.mph()

    assert advantage_negative_split_speed.mph() < 10.0
    assert advantage_negative_split_speed.seconds_per_mile() > 360.0

    caplog.set_level(logging.DEBUG)

    advantage_is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert advantage_is_negative_split

    # For good measure, test failing to detect it without advantage allowed
    is_simple_negative_split = erniegps.get_is_negative_split(
        trackpoints, advantage_allowed=False)
    assert not is_simple_negative_split

    activity = {
        "trackpoints": trackpoints,
        "activity_type": "running",
        "notes": "Test activity created in code",
        "starttime": str(starttime),
        "endtime": str(endtime)
        }
    erniegps.decorate_activity(activity)
    erniegps.process_activity(activity)

    negative_split_depth = activity['negative_split_depth']
    assert negative_split_depth >= 2


def test_adv_split_slow_start_end(caplog):
    """
    Test detecting a negative split when slow points are at the start of a track

    Constant track base + one fast point + one slow point + slow start
    """

    # how many points to use
    #
    point_count = 100

    trackpoints = []
    starttime = datetime.datetime.now(pytz.timezone('US/Eastern'))
    for i in range(0, point_count):
        # constant distance per point but add one hour to the overall track
        point = {
            "distancemiles": i * 10,
            "elapsedtime": "{0}:00:00".format(i + 1),
            "time": str(starttime + datetime.timedelta(hours=i + 1))
        }
        trackpoints.append(point)

    # Zero out first point so the second one is two hours later
    #
    trackpoints[0]["elapsedtime"] = "00:00:00"
    trackpoints[0]["time"] = str(starttime)

    # Add one point with the same distance as between each previous point
    # and only taking 45 minutes instead of an hour
    #
    trackpoints.append({
        "distancemiles": point_count * 10,
        "elapsedtime": "{0}:45:00".format(point_count + 1),
        "time": str(starttime + datetime.timedelta(hours=point_count, minutes=45))
    })

    simple_negative_split_speed = erniegps.get_speed_from_trackpoints(trackpoints)

    simple_is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert simple_is_negative_split

    # Add one point with the same distance as between each previous point
    # and taking two hours instead of one
    #
    endtime = starttime + datetime.timedelta(hours=point_count + 2, minutes=45)
    trackpoints.append({
        "distancemiles": (point_count + 2) * 10,
        "elapsedtime": "{0}:45:00".format(point_count + 2),
        "time": str(endtime)
    })

    advantage_negative_split_speed = erniegps.get_speed_from_trackpoints(trackpoints)

    assert simple_negative_split_speed.mph() > advantage_negative_split_speed.mph()

    assert advantage_negative_split_speed.mph() < 10.0
    assert advantage_negative_split_speed.seconds_per_mile() > 360.0

    caplog.set_level(logging.DEBUG)

    advantage_is_negative_split = erniegps.get_is_negative_split(trackpoints)
    assert advantage_is_negative_split

    # For good measure, test failing to detect it without advantage allowed
    is_simple_negative_split = erniegps.get_is_negative_split(
        trackpoints, advantage_allowed=False)
    assert not is_simple_negative_split

    activity = {
        "trackpoints": trackpoints,
        "activity_type": "running",
        "notes": "Test activity created in code",
        "starttime": str(starttime),
        "endtime": str(endtime)
        }
    erniegps.decorate_activity(activity)
    erniegps.process_activity(activity)

    negative_split_depth = activity['negative_split_depth']
    assert negative_split_depth >= 2
