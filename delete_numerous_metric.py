#!/usr/bin/env python
#
# Delete metric at Numerous 
#
import numerousapp
import argparse


parser = argparse.ArgumentParser(description='Delete Numerous metric')
parser.add_argument('--metric-id', required=True, help='Metric ID')
args = parser.parse_args()

numerousapp.delete_metric(metric_id = args.metric_id)
