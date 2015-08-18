#!/usr/bin/env python
#
# List values for a Numerous metric
#
import numerousapp
import argparse

parser = argparse.ArgumentParser(description='List values for Numerous metric')
parser.add_argument('-n', '--number',
                    help='Number of values to retrieve', type = int, default = 10)
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
  metric = numerousapp.get_metric(metric_id = metric_id);
  print "Metric: " + metric['label']
  printed = 0
  for value in values:
      print "%s: %s" % (value['updated_pretty'], value['value'])
      printed += 1
      if printed > args.number:
        break
