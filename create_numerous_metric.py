#!/usr/bin/env python
#
# Create new metrics at Numerous 
#
import numerousapp
import argparse


parser = argparse.ArgumentParser(description='Create new Numerous metric')
parser.add_argument('-l', '--label', required=True, help='Label')
parser.add_argument('-d', '--description', required=False, help='Description')
args = parser.parse_args()

metric = numerousapp.create_metric(label = args.label, description = args.description)

print "New metric id: %s" % metric['id']


