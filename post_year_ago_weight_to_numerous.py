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
DIFF_METRIC_ID = 414939844104127128

import datetime
from numerousapp import update_metric_value
from ernie import get_withings_weight

def main():

  today = datetime.date.today()

  # Use 52 weeks ago (364 days) so days of the week match
  # 
  one_year_ago = today - datetime.timedelta(days=364)

  one_year_ago_minus_margin = one_year_ago - datetime.timedelta(days = MARGIN_PREVIOUS_WEIGHT)
  today_minus_margin = today - datetime.timedelta(days = MARGIN_PREVIOUS_WEIGHT)

  weights = get_withings_weight(fromdate = one_year_ago_minus_margin, todate = one_year_ago)
  today_weights = get_withings_weight(fromdate = today_minus_margin, todate = today)

  update_metric_value(METRIC_ID, weights[0])
  update_metric_value(DIFF_METRIC_ID, weights[0] - today_weights[0])


if __name__ == '__main__':
  main()

