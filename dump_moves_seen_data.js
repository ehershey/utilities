// dump_moves_seen_data.js
//
//
// Dump information about when stored Moves data has been seen in CSV format
//
// Usage:
// mongo moves dump_moves_seen_data.js

var collection_name = 'activities';

// use moves;

db.getCollection(collection_name).find().toArray().forEach(function(activity) {

  var first_seen = activity.application_metadata.first_seen;
  var start_time = ISODate(activity.startTime.replace(/(\d\d\d\d)(\d\d)(\d\d)/, "$1-$2-$3"));

  var diff_millis = ( first_seen.getTime() - start_time.getTime() )

  var diff_seconds = diff_millis / 1000;

  print(diff_seconds + ", " + activity.activity + ", " + start_time.toString() + ", " + first_seen.toString());

});


