import json
import re
import sys
import urllib2
import numerous_apikey

def make_auth_request(url = None, data = None, headers = None):
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm = 'Numerous',
                                  uri = url, 
                                  user = numerous_apikey.apikey,
                                  passwd='')
    opener = urllib2.build_opener(auth_handler)
    # ...and install it globally so it can be used with urlopen.
    urllib2.install_opener(opener)
    if data and headers:
        return urllib2.Request(url, data, headers)
    else:
        return urllib2.Request(url)

def delete_metric(metric_id):

    url = "https://api.numerousapp.com/v1/metrics/%s" % metric_id

    request = make_auth_request(url)
    request.get_method = lambda: 'DELETE'

    response_body = urllib2.urlopen(request).read()
    return response_body

def get_metric(metric_id):

    url = "https://api.numerousapp.com/v1/metrics/%s" % metric_id

    request = make_auth_request(url)

    response_body = urllib2.urlopen(request).read()
    metric = json.loads(response_body)
    return metric



def get_metrics(labelsearch = ''):

    url = "https://api.numerousapp.com/v1/users/%s/metrics" % numerous_apikey.userid

    request = make_auth_request(url)

    response_body = urllib2.urlopen(request).read()
    metrics = json.loads(response_body)
    labelsearchre = re.compile(labelsearch, flags = re.IGNORECASE)
    return filter(lambda x: labelsearchre.search(x['label']), metrics)


def update_metric_value(metric_id, value, updated = None):

  url = "https://api.numerousapp.com/v1/metrics/%s/events" % metric_id

  values = { "value": value }

  if updated:
      values['updated'] = updated
  else:
      values['onlyIfChanged'] = True

  values = json.dumps(values)
  headers = { 'Content-Type': 'application/json' }

  request = make_auth_request(url, data=values, headers=headers)

  try:
    response_body = urllib2.urlopen(request).read()
    sys.stderr.write(response_body)
  except urllib2.URLError as e:
    sys.stderr.write("Error updating value to %s via url: %s: %s\n" % (value, url, e))

def get_metric_values(metric_id):
    
  url = "https://api.numerousapp.com/v1/metrics/%s/events" % metric_id

  request = make_auth_request(url)
 
  try:
    response_body = urllib2.urlopen(request).read()
    response = json.loads(response_body)
    if 'events' in response:
        return response['events']
    else:
      return []
  except urllib2.URLError as e:
    sys.stderr.write("Error fetching value via url %s: %s\n" % (url, e))

   
def get_metric_value(metric_id):
    values = get_metric_values(metric_id)
    if len(values) > 0:
        return values[0]
    else:
        return None

def create_metric(label, description, kind = "number", value = None, units = None, private = True, writeable = False ):

    url = "https://api.numerousapp.com/v1/metrics"

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
    request = make_auth_request(url, data=values, headers=headers)

    try:
        response_body = urllib2.urlopen(request).read()
        print response_body
        response = json.loads(response_body)
        return response['events'][0]['value']
    except urllib2.URLError as e:
        sys.stderr.write("Error fetching value via url %s: %s\n" % (url, e))

