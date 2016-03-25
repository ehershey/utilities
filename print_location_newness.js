// update gps_log data with the number of nearby points that occurred before it
//
// usage :
// mongo ernie_org < print_location_newness.js
//
var criteria = { entry_date: { $gte: new Date(2014,03,1,0,0,0,0) } };
var distance_required_to_be_new_meters = 25;

var update_previous_nearby = function(item) {
  var earlier_criteria =
  {
    entry_date: { "$lt": item.entry_date },
    loc: { "$nearSphere": { "$geometry": item.loc, "$maxDistance": distance_required_to_be_new_meters } }
  };
  print(db.gps_log.find(earlier_criteria).count());
}

db.gps_log.find(criteria).forEach(update_previous_nearby);
