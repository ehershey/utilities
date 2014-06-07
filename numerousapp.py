import json
import sys
import urllib2
import numerous_apikey

def get_metrics():

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
    return metrics_json


def update_metric_value(metric_id, value):
  auth_handler = urllib2.HTTPBasicAuthHandler()

  url = "https://api.numerousapp.com/v1/metrics/%s/events" % metric_id

  auth_handler.add_password(realm = 'Numerous', uri = url, user = numerous_apikey.apikey, passwd='')
  opener = urllib2.build_opener(auth_handler)
  # ...and install it globally so it can be used with urlopen.
  urllib2.install_opener(opener)

  values = """ { "value": %s, "onlyIfChanged": true } """ % value
  headers = { 'Content-Type': 'application/json' }
  request = urllib2.Request(url, data=values, headers=headers)

  try:
    response_body = urllib2.urlopen(request).read()
    sys.stderr.write(response_body)
  except urllib2.URLError as e:
    sys.stderr.write("Error updating value to %s via url: %s: %s\n" % (value, url, e))

def get_metric_value(metric_id):
  auth_handler = urllib2.HTTPBasicAuthHandler()

  url = "https://api.numerousapp.com/v1/metrics/%s/events" % metric_id

  auth_handler.add_password(realm = 'Numerous', uri = url, user = numerous_apikey.apikey, passwd='')
  opener = urllib2.build_opener(auth_handler)
  # ...and install it globally so it can be used with urlopen.
  urllib2.install_opener(opener)

  # values = """ { "value": %s, "onlyIfChanged": true } """ % value
  # values = """ {} """
  # headers = { 'Content-Type': 'application/json' }
  #request = urllib2.Request(url, data=values, headers=headers)
  request = urllib2.Request(url)

  try:
    response_body = urllib2.urlopen(request).read()
    response = json.loads(response_body)
    return response['events'][0]['value']
  except urllib2.URLError as e:
    sys.stderr.write("Error fetching value via url %s: %s\n" % (url, e))

def create_metric(label, description, kind = "number", value = None, units = None, private = True, writeable = False ):
    auth_handler = urllib2.HTTPBasicAuthHandler()

    url = "https://api.numerousapp.com/v1/metrics"

    auth_handler.add_password(realm = 'Numerous', uri = url, user = numerous_apikey.apikey, passwd='')
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
        "private": private,
        "writeable": writeable
    }

    values = json.dumps(values)
    headers = { 'Content-Type': 'application/json' }
    request = urllib2.Request(url, data=values, headers=headers)

    try:
        response_body = urllib2.urlopen(request).read()
        response = json.loads(response_body)
        return response['events'][0]['value']
    except urllib2.URLError as e:
        sys.stderr.write("Error fetching value via url %s: %s\n" % (url, e))


