#!/usr/bin/env python
"""
Test erniegps module
"""


import erniegps
import m26
import pytest

#def test_error_on_too_few_trackpoints():
  #with pytest.raises(erniegps.ActivityException):
    #erniegps.get_speed_from_trackpoints([])
  #with pytest.raises(erniegps.ActivityException):
    #erniegps.get_speed_from_trackpoints([{}])


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
    activity = erniegps.read_activity('/home/ernie/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx')
    activity = erniegps.read_activity('/home/ernie/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx')
    trackpoints = activity['trackpoints']
    assert len(trackpoints) == 8


def test_trackpoint_split():
    activity = erniegps.read_activity('/home/ernie/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx')
    trackpoints = activity['trackpoints']
    (first_half_trackpoints, last_half_trackpoints) = erniegps.split_trackpoints(trackpoints)
    assert len(first_half_trackpoints) == 2
    assert len(last_half_trackpoints) == 6


def test_single_depth():
    activity = erniegps.read_activity('/home/ernie/Dropbox/Apps/tapiriik/2014-04-29_Walking (1).tcx')
    activity = erniegps.process_activity(activity)
    assert activity.get('is_negative_split') is True
    assert activity.get('negative_split_depth') == 1
