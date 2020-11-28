#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test auto walking

To run:
    $ pytest-3
"""

import datetime
import logging
import os
import pytz
import m26
import erniegps
import gpx_to_walk_tracks

base_dir = '{0}/Dropbox/Misc/Arc Export/Export/GPX/Daily/'.format(os.environ['HOME'])


def test_one_track_all_day():
    """
    Test days with one single activity, including some stops
    """

    for date in ['2020-10-22', '2020-10-19', '2020-07-29']:

        gpx_file = base_dir + date + '.gpx'

        # logging.getLogger().setLevel(getattr(logging, "DEBUG"))
        # logging.debug("Debug logging enabled")

        gpx_to_walk_tracks.init()
        tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                        skip_strava=True)

        assert len(tracks) == 1


def test_leaked_state():
    """
    make sure the same thing again still works (no leaked state)
    """
    gpx_file = base_dir + '2020-10-19.gpx'

    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava_auto_walking=True)

    assert len(tracks) == 1

    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file)
    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file)

    # should be 0 since our activity should be there
    assert len(tracks) == 0

    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava=True)
    assert len(tracks) == 1


def test_spain_long_run():
    """
    Verify we don't try to upload a long walking track overlapping a strava-recorded
    long running track in spain
    """

    # logging.getLogger().setLevel(getattr(logging, "DEBUG"))
    # logging.debug("Debug logging enabled")

    # no strava at all - long run + two walks
    gpx_file = base_dir + '2018-11-18.gpx'
    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava=True)
    assert len(tracks) == 3
    assert erniegps.get_track_distance(tracks[0]) > 25000
    assert 1000 < erniegps.get_track_distance(tracks[1]) < 1500
    assert 1000 < erniegps.get_track_distance(tracks[2]) < 1500

    # no strava auto walk uploads - walk before long run, walk after and same two misc
    # walks as above. requires strava data in db
    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava_auto_walking=True)
    assert len(tracks) == 4
    assert 100 < erniegps.get_track_distance(tracks[0]) < 400
    assert 100 < erniegps.get_track_distance(tracks[1]) < 400
    assert 1000 < erniegps.get_track_distance(tracks[2]) < 1500
    assert 1000 < erniegps.get_track_distance(tracks[3]) < 1500


def test_home_long_run():
    """
    Misc aspects of a long run day at home
    """
    gpx_file = base_dir + '2020-11-21.gpx'
    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava=True)
    assert(len(tracks)) == 1


def test_no_subway():
    """
    don't count riding the subway as walking
    """
    gpx_file = base_dir + '2017-10-31.gpx'
    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava=True)
    assert(len(tracks)) == 2
    assert 3000 < erniegps.get_track_distance(tracks[0]) < 4000
    assert 10000 < erniegps.get_track_distance(tracks[1]) < 15000


def test_not_too_short():
    """
    Don't log a 200 foot walk
    """
    gpx_file = base_dir + '2020-11-22.gpx'
    gpx_to_walk_tracks.init()
    tracks = gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                    skip_strava_auto_walking=True)
    assert len(tracks) == 1


def fresh_auto_tracks(track_date):
    """
    Given a date string, return all auto walking tracks that would be created,
    ignoring any existing auto walking tracks (not ignoring other Strava
    activities)
    """
    gpx_file = f"{base_dir}{track_date}.gpx"
    gpx_to_walk_tracks.init()
    return gpx_to_walk_tracks.get_combined_tracks(gpx_file=gpx_file,
                                                  skip_strava_auto_walking=True)


def test_no_long_drive():
    """
    165 mile drive through new jersey somehow registered as a long walk
    """
    for track in fresh_auto_tracks('2020-10-03'):
        assert erniegps.get_track_distance(track) < 10000


def test_not_walking_to_newark():
    """
    Old absurd walking tracks from old version of code was 15 miles to Newark airport
    and 6 miles from home to midtown. This makes sure neither are walking tracks
    """
    for track in fresh_auto_tracks('2019-10-07'):
        assert erniegps.get_track_distance(track) < 2000
