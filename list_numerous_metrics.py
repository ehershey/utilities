#!/usr/bin/env python
#
# List user metrics from Numerous 
#
import numerousapp

metrics = numerousapp.get_metrics()

for metric in metrics:
    print "label: %s" % metric['label']
    print "id: %s" % metric['id']
    print "last_value: %s" % numerousapp.get_metric_value(metric['id'])
    print ""
