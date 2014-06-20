#!/usr/bin/env python
#
# List values for a Numerous metric
#
import numerousapp
import argparse

parser = argparse.ArgumentParser(description='List values for a Numerous metric')
parser.add_argument('--metric-id', required=True, help='Metric ID')
args = parser.parse_args()

values = numerousapp.get_metric_values(args.metric_id);
for value in values:
    print value


