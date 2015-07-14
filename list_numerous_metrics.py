#!/usr/bin/env python
#
# List user metrics from Numerous
#
import argparse
import codecs
import numerousapp
import sys


parser = argparse.ArgumentParser(description='List Numerous metrics')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-l', '--labelsearch', help='Label regular expression search', default='')
group.add_argument('-m', '--metric-id', help='Metric ID')
parser.add_argument('-v', '--verbose', action='store_true', help='Include some extra details')
parser.add_argument('-d', '--debug', action='store_true', help='Include a lot of extra details')
args = parser.parse_args()


if args.labelsearch:
  metrics = numerousapp.get_metrics(labelsearch = args.labelsearch)
else:
  metrics = [ numerousapp.get_metric(metric_id = args.metric_id) ]


for metric in metrics:
    # print metric
    print "label: %s" % metric['label']
    print "description: %s" % metric['description'].encode('ascii', 'ignore')
    print "id: %s" % metric['id']
    print "last_value: %s" % metric['value']
    if args.verbose:
        if 'photoURL' in metric:
            print "photoURL: %s" % metric['photoURL']
        print "updated: %s" % metric['updated_pretty']
    if args.debug:
        print "Raw JSON: %s" % metric
    print ""
