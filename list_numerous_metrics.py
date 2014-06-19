#!/usr/bin/env python
#
# List user metrics from Numerous 
#
import numerousapp
import codecs

metrics = numerousapp.get_metrics()

for metric in metrics:
    # print metric
    print "label: %s" % metric['label']
    print "description: %s" % metric['description'].encode('ascii', 'ignore')
    print "id: %s" % metric['id']
    print "last_value: %s" % numerousapp.get_metric_value(metric['id'])['value']
    print ""
