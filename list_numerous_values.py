#!/usr/bin/env python
#
# List values for a Numerous metric
#
import numerousapp
import argparse
import datetime

parser = argparse.ArgumentParser(description='List values for a Numerous metric')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-m', '--metric-id', help='Metric ID')
group.add_argument('-l', '--labelsearch', help='Metric label regular expression search')
args = parser.parse_args()

if args.labelsearch:
  metric_ids = [ metric['id'] for metric in numerousapp.get_metrics(labelsearch = args.labelsearch) ]
else:
  metric_ids = [ args.metric_id ]

for metric_id in metric_ids:
  values = numerousapp.get_metric_values(metric_id = metric_id);
  for value in values:
      print datetime.datetime.strptime(value['updated'], '%Y-%m-%dT%H:%M:%S.%fZ')
      print value['value']
      print ""


