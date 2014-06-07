#!/usr/bin/env python
#
# Create new metrics at Numerous 
#
import ernie
import argparse


parser = argparse.ArgumentParser(description='Create new Numerous metric')
parser.add_argument('--label', type=string, required=True, help='Label')
parser.add_argument('--description', type=string, required=True, help='Description')
args = parser.parse_args()

metric = ernie.create_numerous_metric(label = label, description = description)

print "New metric id: %s" % metric['id']


