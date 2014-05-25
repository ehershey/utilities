#!/usr/bin/env python
# vim: set filetype=python expandtab tabstop=2 softtabstop=2 shiftwidth=2 autoindent smartindent:
#
# Post weight from one year ago to Numerous
#
# If there's no measurement from exactly one year ago, post
# the latest previous measurement up to <MARGIN_PREVIOUS_WEIGHT> 
# days back in time


# How many days back from the target date to search before giving up
#
MARGIN_PREVIOUS_WEIGHT = 14

METRIC_ID = 2541720541413967188

import datetime
from ernie import post_numerous_metric, get_withings_weight

def main():

  today = datetime.date.today()

  one_year_ago = today - datetime.timedelta(days=365)

  one_year_ago_plus_margin = one_year_ago - datetime.timedelta(days = MARGIN_PREVIOUS_WEIGHT)

  weights = get_withings_weight(fromdate = one_year_ago_plus_margin, todate = one_year_ago)

  post_numerous_metric(METRIC_ID, weights[0])


if __name__ == '__main__':
  main()

