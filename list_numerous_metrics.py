#!/usr/bin/env python
#
# List user metrics from Numerous 
#
import ernie
import json
import urllib2
import numerous_apikey

if __name__ == '__main__':

    url = "https://api.numerousapp.com/v1/users/%s/metrics" % numerous_apikey.userid

    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm = 'Numerous',
                                  uri = url, 
                                  user = numerous_apikey.apikey,
                                  passwd='')
    opener = urllib2.build_opener(auth_handler)
    # ...and install it globally so it can be used with urlopen.
    urllib2.install_opener(opener)

    request = urllib2.Request(url)
    response_body = urllib2.urlopen(request).read()
    metrics_json = json.loads(response_body)
    for metric in metrics_json:
      print "label: %s" % metric['label']
      print "id: %s" % metric['id']
      print "last_value: %s" % ernie.get_numerous_metric_value(metric['id'])
      print ""
