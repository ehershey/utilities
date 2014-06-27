#!/usr/bin/env python
#
# List user metrics from Numerous 
#
import numerousapp
import codecs
import argparse


parser = argparse.ArgumentParser(description='List Numerous metrics')
parser.add_argument('-l', '--labelsearch', help='Label regular expression search', default='')
parser.add_argument('-v', '--verbose', action='store_true', help='Include some extra details')
parser.add_argument('-d', '--debug', action='store_true', help='Include a lot of extra details')
args = parser.parse_args()



metrics = numerousapp.get_metrics(args.labelsearch)

for metric in metrics:
    # print metric
    print "label: %s" % metric['label']
    print "description: %s" % metric['description'].encode('ascii', 'ignore')
    print "id: %s" % metric['id']
    print "last_value: %s" % numerousapp.get_metric_value(metric['id'])['value']
    if args.verbose:
        if 'photoURL' in metric:
            print "photoURL: %s" % metric['photoURL']
        print "updated: %s" % metric['updated']
    if args.debug:
        print "Raw JSON: %s" % metric
    print ""
