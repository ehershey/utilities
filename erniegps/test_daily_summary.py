#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test daily summary generation

To run:
    $ pytest-3
"""

import datetime
import logging
import os
import pytz
import m26
import erniegps
import gpx_to_daily_summary

base_dir = '{0}/Dropbox/Misc/Arc Export/Export/GPX/Daily/'.format(os.environ['HOME'])


def test_string_in_track():
    """
    Make sure normalization works with date string in DB (old way)
    """

    session = {"trackPoints": [{"dateTime": "2021-02-03 01:28:35"}]}
    track = {}
    track_start = datetime.datetime(2021, 2, 3, 1, 28, 35)

    normalized_start, normalized_end = \
        erniegps.get_normalized_livetrack_start_end(session, track, track_start)

    assert normalized_start.tzinfo is not None
    assert normalized_end.tzinfo is not None


def test_date_in_track():
    """
    Make sure normalization works with date object in DB now that we're using real go types
    in receiver code
    """

    session = {"trackPoints": [{"dateTime": datetime.datetime(2021, 2, 3, 1, 28, 35)}]}
    track = {}
    track_start = datetime.datetime(2021, 2, 3, 1, 28, 35)

    normalized_start, normalized_end = \
        erniegps.get_normalized_livetrack_start_end(session, track, track_start)

    assert normalized_start.tzinfo is not None
    assert normalized_end.tzinfo is not None


def test_timezone_crossing():
    """
    Test putting a livetrack from late yesterday in EST in the right date
    """

    gpx_file = base_dir + '2020-11-05-empty.gpx'

    gpx_to_daily_summary.init()
    summary = gpx_to_daily_summary.get_summary(
            gpx_file=gpx_file,
            date='2020-11-05',
            skip_strava=True)
    assert summary is not None
    assert summary["Calories"] == 0


def test_intuit_date():
    """
    Make sure the summary that comes back is from the right date
    """

    gpx_file = base_dir + '2020-11-05-empty.gpx'

    gpx_to_daily_summary.init()
    summary = gpx_to_daily_summary.get_summary(
            gpx_file=gpx_file,
            skip_strava=True)
    assert summary is not None
    assert summary["Verbose Date"] == '2020-11-05'


def test_unique_summary_dates():
    """
    ensure we don't duplicate summary dates (and thus omit data in default one-only case
    """
    gpx_file = base_dir + '2018-12-30.gpx'
    gpx_to_daily_summary.init()
    summaries = gpx_to_daily_summary.get_summaries(
            gpx_file=gpx_file,
            allow_multiple=True)
    assert len(summaries) == len(set([summary['Verbose Date'] for summary in summaries]))
