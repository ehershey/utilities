#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test erniegps module
"""


import os
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

    assert erniegps.get_speed_from_trackpoints([{"distancemiles": 50}]).seconds_per_mile() == 0
    assert erniegps.get_speed_from_trackpoints([{}]).mph() == 0
    assert erniegps.get_speed_from_trackpoints([{}]).seconds_per_mile() == 0
    assert erniegps.get_speed_from_trackpoints([]).mph() == 0
    assert erniegps.get_speed_from_trackpoints([]).seconds_per_mile() == 0


def test_zero_distance():
    assert erniegps.get_distance_from_trackpoints([{"distancemiles": 50}]).as_miles() == m26.Distance(0).as_miles()
    assert erniegps.get_distance_from_trackpoints([{}]).as_miles() == m26.Distance(0).as_miles()
    assert erniegps.get_distance_from_trackpoints([{}, {}]).as_miles() == m26.Distance(0).as_miles()
    assert erniegps.get_distance_from_trackpoints([]).as_miles() == m26.Distance(0).as_miles()


def test_double_read_single_activity():
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(os.environ['HOME']))
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(os.environ['HOME']))
    trackpoints = activity['trackpoints']
    assert len(trackpoints) == 8


def test_trackpoint_split():
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(os.environ['HOME']))
    trackpoints = activity['trackpoints']
    (first_half_trackpoints, last_half_trackpoints) = erniegps.split_trackpoints(trackpoints)
    assert len(first_half_trackpoints) == 2
    assert len(last_half_trackpoints) == 6


def test_no_negative_split():
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx'.format(os.environ['HOME']))
    activity = erniegps.process_activity(activity)
    assert activity.get('is_negative_split') is False
    assert activity.get('negative_split_depth') == 0


def test_empty_distance():
    """ This track has a trackpoint with no distance that will break an unpatched ggps module """
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2011-02-03_Running.tcx'.format(os.environ['HOME']))
    trackpoints = activity['trackpoints']


def test_get_activity_type():
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2017-05-27_New York Running_Running.tcx'.format(os.environ['HOME']))
    assert activity['activity_type'] == "Running"
    assert activity['notes'] == "New York Running"


def test_has_verbose_starttime():
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2017-05-27_New York Running_Running.tcx'.format(os.environ['HOME']))
    assert type(activity['verbose_starttime']) == str
    assert activity['verbose_starttime'] == '19:03'


def test_has_verbose_distance():
    activity = erniegps.read_activity('{0}/Dropbox/Apps/tapiriik/2017-05-27_New York Running_Running.tcx'.format(os.environ['HOME']))
    assert type(activity['verbose_distance']) == str
    assert activity['verbose_distance'] == '10.13 miles'


def test_handle_unicode_notes_char():
    activity = erniegps.read_activity(u'{0}/Dropbox/Apps/tapiriik/2016-06-01_Słomczyn Running_Running.tcx'.format(os.environ['HOME']))
