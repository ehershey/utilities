#!/usr/bin/env python
#
# List values for a Numerous metric
#
import numerousapp
import argparse
import datetime

parser = argparse.ArgumentParser(description='List values for a Numerous metric')
parser.add_argument('--metric-id', required=True, help='Metric ID')
args = parser.parse_args()

values = numerousapp.get_metric_values(args.metric_id);
for value in values:
    print datetime.datetime.strptime(value['updated'], '%Y-%m-%dT%H:%M:%S.%fZ')
    print value['value']
    print ""


