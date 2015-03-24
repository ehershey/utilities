#!/usr/bin/env mongo
db = db.getSiblingDB('ernie_org');
// update gps_log data with the number of nearby points that occurred before it
//
//
// usage :
// mongo ernie_org < print_location_newness.js
//
//var criteria = { entry_date: { $gte: new Date(2014,03,15,0,0,0,0) }, previous_point_count: { "$exists": false } };
var criteria = { previous_point_count: { "$exists": false } };
var distance_required_to_be_new_meters = 25;

var update_previous_nearby = function(item) {
  var earlier_criteria =
  {
    entry_date: { "$lt": item.entry_date },
    loc: { "$nearSphere": { "$geometry": item.loc, "$maxDistance": distance_required_to_be_new_meters } }
  };
  var count = db.gps_log.find(earlier_criteria).count();
  item.previous_point_distance = distance_required_to_be_new_meters;
  item.previous_point_count = count;
  db.gps_log.save(item);
  print(".");
}


var curs = db.gps_log.find(criteria); null;
var count = curs.count();
print("total: " + count);
curs.forEach(update_previous_nearby);
