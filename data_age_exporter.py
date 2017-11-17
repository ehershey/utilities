#!/usr/bin/env python
#
# Serve personal data metrics
# Age of updates
# Thermostat info
# Withings info
# Moves App info
from prometheus_client import start_http_server, Summary, Gauge
import random
import time
import pymongo

HTTP_PORT=8001
SLEEP_DURATION=30

humidity_gauge = Gauge('home_humidity', 'Humidity at home')
target_temperature_f_gauge = Gauge('home_target_temperature_f', 'Target Temperature at home')
ambient_temperature_f_gauge = Gauge('home_ambient_temperature_f', 'Ambient Temperature at home')

client = pymongo.MongoClient("mongodb://localhost:27017")
nest_database = client.get_database("nest")
thermostat_log = nest_database.get_collection("thermostat_log")


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(HTTP_PORT)
    # Generate some requests.
    import time
    while True:
      result = thermostat_log.find().sort([('_id', -1)]).limit(1)[0]
      last_connection = result.get('last_connection')
      print("last_connection: %s" % last_connection)
      humidity = result.get('humidity')
      print("humidity: %s" % humidity)
      humidity_gauge.set(humidity)
      target_temperature_f = result.get('target_temperature_f')
      print("target_temperature_f: %s" % target_temperature_f)
      target_temperature_f_gauge.set(target_temperature_f)
      ambient_temperature_f = result.get('ambient_temperature_f')
      print("ambient_temperature_f: %s" % ambient_temperature_f)
      ambient_temperature_f_gauge.set(ambient_temperature_f)
      print("sleeping %s seconds" % SLEEP_DURATION)
      time.sleep(SLEEP_DURATION)
