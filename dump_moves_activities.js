// dump_moves_activities.js
//
//
// Dump Moves activities in CSV format
//
// Usage: 
// mongo moves dump_moves_activities.js

var collection_name = 'activities';

// use moves;

print("Activity Type, Start Time, Start Longitude, Start Latitude, End Time, End Longitude, End Latitude");

db.getCollection(collection_name).find().sort({startTime: 1}).toArray().forEach(function(activity) { 

  var start_time = ISODate(activity.startTime.replace(/(\d\d\d\d)(\d\d)(\d\d)/, "$1-$2-$3"));
  var end_time = ISODate(activity.endTime.replace(/(\d\d\d\d)(\d\d)(\d\d)/, "$1-$2-$3"));

  var start_trackpoint = activity.trackPoints[0];
  if(start_trackpoint) { 
    var end_trackpoint = activity.trackPoints[activity.trackPoints.length - 1];
    var end_longitude = end_trackpoint.lon;
    var end_latitude = end_trackpoint.lat;
    var start_longitude = start_trackpoint.lon;
    var start_latitude = start_trackpoint.lat;
  }
  else
  {
    var end_longitude = "";
    var end_latitude = "";
    var start_longitude = "";
    var start_latitude = "";
  }

  print(activity.activity + ", " + start_time.toString() + ", " + start_longitude + ", " + start_latitude + ", " + end_time.toString() + ", " + end_longitude + ", " + end_latitude);

});


