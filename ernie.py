import numerous_apikey
import sys
import urllib2

def post_numerous_metric(metric_id, value):
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


