# numerousapp.py
#
# Python interface to Numerous App metrics
#
#
# By Ernie Hershey
#
import datetime
import json
import re
import sys
import urllib2
import numerous_apikey

base_url = "https://api.numerousapp.com/v1"

def make_auth_request(url=None, data=None, headers=None):
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm='Numerous',
                              uri=url,
                              user=numerous_apikey.apikey,
                              passwd='')
    opener=urllib2.build_opener(auth_handler)
    # ...and install it globally so it can be used with urlopen.
    urllib2.install_opener(opener)
    if data and headers:
        return urllib2.Request(url, data, headers)
    else:
        return urllib2.Request(url)

def delete_metric(metric_id):

    url="%s/metrics/%s" % (base_url, metric_id)

    request=make_auth_request(url)
    request.get_method=lambda: 'DELETE'

    response_body=urllib2.urlopen(request).read()
    return response_body

def get_metric(metric_id):

    url="%s/metrics/%s" % (base_url, metric_id)

    request=make_auth_request(url)

    response_body=urllib2.urlopen(request).read()
    metric=json.loads(response_body)
    return metric



def get_metrics(labelsearch=''):

    url="%s/users/%s/metrics" % (base_url, numerous_apikey.userid)

    request=make_auth_request(url)

    response_body=urllib2.urlopen(request).read()
    metrics=json.loads(response_body)
    labelsearchre=re.compile(labelsearch, flags=re.IGNORECASE)
    for metric in metrics:
        metric['updated_pretty']=datetime.datetime.strptime(metric['updated'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d %H:%M:%S")
    return filter(lambda x: labelsearchre.search(x['label']), metrics)


def update_metric_value(metric_id, value, updated=None):

  url="%s/metrics/%s/events" % (base_url, metric_id)

  values={ "value": value }

  if updated:
      values['updated']=updated
  else:
      values['onlyIfChanged']=True

  values=json.dumps(values)
  headers={ 'Content-Type': 'application/json' }

  request=make_auth_request(url, data=values, headers=headers)

  try:
    response_body=urllib2.urlopen(request).read()
    sys.stderr.write(response_body)
  except urllib2.URLError as e:
    sys.stderr.write("Error updating value to %s via url: %s: %s\n" % (value, url, e))

def get_metric_values(metric_id):

  url="%s/metrics/%s/events" % (base_url, metric_id)

  request=make_auth_request(url)

  try:
    response_body=urllib2.urlopen(request).read()
    response=json.loads(response_body)
    if 'events' in response:
      values=[]
      for value in response['events']:
        value['updated_pretty']=datetime.datetime.strptime(value['updated'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d %H:%M:%S")
        values.append(value)
      return values
    else:
      return []
  except urllib2.URLError as e:
    sys.stderr.write("Error fetching value via url %s: %s\n" % (url, e))


def get_metric_value(metric_id):
    values=get_metric_values(metric_id)
    if len(values) > 0:
        return values[0]
    else:
        return None

def create_metric(label, description, kind="number", value=None, units=None, private=True, writeable=False ):

    url="https://api.numerousapp.com/v1/metrics"

    # required parameters:
    # label
    # description
    # kind ("number", "currency", "percent", or "timer")
    # units
    values={
        "label": label,
        "description": description,
        "kind": kind,
        "currencySymbol": "$",
        "value": value,
        "units": units,
        "private": private,
        "writeable": writeable
    }

    values=json.dumps(values)
    headers={ 'Content-Type': 'application/json' }
    request=make_auth_request(url, data=values, headers=headers)

    try:
        response_body=urllib2.urlopen(request).read()
        print response_body
        response=json.loads(response_body)
        return response
    except urllib2.URLError as e:
        sys.stderr.write("Error fetching value via url %s: %s\n" % (url, e))


