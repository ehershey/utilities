#!/usr/bin/env python
# vim: set filetype=python expandtab tabstop=2 softtabstop=2 shiftwidth=2 autoindent smartindent:
#
# Update a Numerous App Metric
#

import argparse
import numerousapp


parser = argparse.ArgumentParser(description='Update Numerous metric')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-m', '--metric-id', help='Metric ID')
group.add_argument('-l', '--labelsearch', help='Metric label regular expression search')
parser.add_argument('-n', '--number', help='New Value', required = True)
parser.add_argument('-v', '--verbose', action='store_true', help='Include some extra details')
parser.add_argument('-d', '--debug', action='store_true', help='Include a lot of extra details')
args = parser.parse_args()

if args.labelsearch:
  metric_ids = [ metric['id'] for metric in numerousapp.get_metrics(labelsearch = args.labelsearch) ]
else:
  metric_ids = [ args.metric_id ]

if len(metric_ids) > 1:
  print("Multiple metrics in update list - use narrower criteria")
  exit(3)



def main():
  metric_id = metric_ids[0]
  metric = numerousapp.get_metric(metric_id = metric_id);
  print "Metric: " + metric['label']
  if args.verbose:
    print "Old Value: " + str(metric['value'])
  if args.debug:
    print "Raw JSON: %s" % metric

  numerousapp.update_metric_value(metric_id, args.number)

  if args.verbose:
    metric = numerousapp.get_metric(metric_id = metric_id);
    print "New Value: " + str(metric['value'])

if __name__ == '__main__':
  main()

