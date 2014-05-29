#!/usr/bin/env python
#
# Create new metrics at Numerous 
#
import json
import urllib2
import numerous_apikey
import argparse


parser = argparse.ArgumentParser(description='Create new Numerous metric')
parser.add_argument('--label', type=string, required=True, help='Label')
parser.add_argument('--description', type=string, required=True, help='Description')
args = parser.parse_args()




url = "https://api.numerousapp.com/v1/metrics"

auth_handler = urllib2.HTTPBasicAuthHandler()
auth_handler.add_password(realm = 'Numerous',
                              uri = url, 
                              user = numerous_apikey.apikey,
                              passwd='')
opener = urllib2.build_opener(auth_handler)
# ...and install it globally so it can be used with urlopen.
urllib2.install_opener(opener)

# required parameters: 
# label
# description
# kind ("number", "currency", "percent", or "timer")
# units
values = {
    "label": label,
    "description": description,
    "kind": kind,
    "currencySymbol": "$",
    "value": value,
    "units": units,
    "private": true,
    "writeable": false
}

request = urllib2.Request(url)
response_body = urllib2.urlopen(request).read()
metrics_json = json.loads(response_body)
for metric in metrics_json:
  print "label: %s" % metric['label']
  print "id: %s" % metric['id']
  print ""
