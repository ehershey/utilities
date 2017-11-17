#!/usr/bin/env python
from prometheus_client import start_http_server, Summary, Gauge
import random
import time
import pymongo

HTTP_PORT=8000
SLEEP_DURATION=30

humidity_gauge = Gauge('home_humidity', 'Humidity at home')
target_temperature_f_gauge = Gauge('home_target_temperature_f', 'Target Temperature at home')
ambient_temperature_f_gauge = Gauge('home_ambient_temperature_f', 'Humidity at home')
# g.set_function(lambda: len(my_dict))

#connection = pymongo.Connection('localhost', 27017)
#db = connection.nest
#humidity = db.thermostat_log.find_one(
    #{"date": today.strftime("%B %-d, %Y")})
client = pymongo.MongoClient("mongodb://localhost:27017")
database = client.get_database("nest")
collection = database.get_collection("thermostat_log")


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(HTTP_PORT)
    # Generate some requests.
    import time
    while True:
      result = collection.find().sort([('_id', -1)]).limit(1)
      humidity = result[0].get('humidity')
      print("humidity: %s" % humidity)
      humidity_gauge.set(humidity)
      target_temperature_f = result[0].get('target_temperature_f')
      print("target_temperature_f: %s" % target_temperature_f)
      target_temperature_f_gauge.set(target_temperature_f)
      ambient_temperature_f = result[0].get('ambient_temperature_f')
      print("ambient_temperature_f: %s" % ambient_temperature_f)
      ambient_temperature_f_gauge.set(ambient_temperature_f)
      print("sleeping %s seconds" % SLEEP_DURATION)
      time.sleep(SLEEP_DURATION)
