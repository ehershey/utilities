#!/usr/bin/env node
'use strict';
// Save moves json on stdin to mongodb
//
// Entities:
// 1) A day worth of activity
//    Collection: dates
//    Key: date
// 2) Segments
//    Collection: segments
//    Key: startTime
// 3) Activities
//    Collection: activities
//    Key: startTime
//
// For each entity, add fields:
// 1) application_metadata: { first_seen: <timestamp>, last_seen: <timestamp>, seen_count: <count> }
//
//
//
// Example usage in crontab:
// */5 * * * * curl --silent "https://api.moves-app.com/api/1.1/user/activities/daily?pastDays=7&access_token=$MOVES_ACCESS_TOKEN"  | ~ernie/git/utilities/save_moves_activities.js > /tmp/save_moves_activities.log 2>&1


var mongodb = require('mongodb');
var request = require('request');

var moves_access_token = process.env.MOVES_ACCESS_TOKEN;

if(!moves_access_token) {
  console.error("Environment variable not set: MOVES_ACCESS_TOKEN");
  process.exit(2);
}




// set database options
//
var dbname = "moves";
var dbserver = "localhost";
var dbport = 27017;

var dbuser = '';
var dbpass = '';

var dboptions = '';


// process database options
//

var dbuserpass = '';

if(dbuser && dbpass)
{
  dbuserpass = dbuser + ':' + dbpass + '@';
}

if(dboptions) {
  dboptions = '?' + dboptions;
}

var dburl = 'mongodb://' + dbuserpass + dbserver + ':' + dbport + '/' + dbname + dboptions;

console.log('dburl: ' + dburl);

var MongoClient = mongodb.MongoClient;

// read json on stdin into memory
//

var stdin_chunks = [];

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});


var now = new Date();

var last_seen = now;

var wrote_date_count = 0;
var total_date_count = 0;
var wrote_segment_count = 0;
var total_segment_count = 0;
var wrote_activity_count = 0;
var total_activity_count = 0;
var incoming_json;


function cleanup_db_connection(db) {
  setTimeout(function() {
    if(wrote_activity_count === total_activity_count && wrote_date_count === total_date_count && wrote_segment_count === total_segment_count)
    {
      console.log('calling db.close()');
      db.close();
    }
  }, 5000);
}


function save_date(db,date)
{

  var collection = db.collection("dates");

  collection.find({ date: date.date}, function(err, cursor)
  {
    if (err) { throw err; }


    console.log("date.date: " + date.date);

    console.log('calling find() on dates');

    var first_seen;
    var seen_count;


    cursor.toArray(function(err, result)
    {
      if (err) { throw err; }


      console.log('result.length: ' + result.length);

      if(result.length === 0)
      {
        first_seen = now;
        seen_count = 1;
      }
      else if(result.length === 1)
      {
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
      }
      else
      {
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
        throw("too many results!");
      }

      console.log('first_seen: ' + first_seen);
      console.log('last_seen: ' + last_seen);
      console.log('seen_count: ' + seen_count);

      date.application_metadata = { first_seen: first_seen, last_seen: last_seen, seen_count: seen_count };


      console.log('attempting to save date: ' + date);

      collection.update({date: date.date}, date, {upsert:true, w: 1}, function(err, result)
      {
        if (err) { throw err; }
        // collection.insert(date, {upsert:true, w: 1}, function(err, result) {

        console.log("saved date, result.result:");
        console.log(result.result);
        wrote_date_count++;
        cleanup_db_connection(db);

      });
    });
  });
}

function save_segment(db,segment)
{

  var collection = db.collection("segments");

  collection.find({ startTime: segment.startTime}, function(err, cursor)
  {
    if (err) { throw err; }

    console.log("segment.startTime: " + segment.startTime);

    console.log('calling find() on segments');

    var first_seen;
    var seen_count;

    cursor.toArray(function(err, result)
    {
      if (err) { throw err; }

      console.log('result.length: ' + result.length);

      if(result.length === 0)
      {
        first_seen = now;
        seen_count = 1;
      }
      else if(result.length === 1)
      {
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
      }
      else
      {
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
        throw("too many results!");
      }

      console.log('first_seen: ' + first_seen);
      console.log('last_seen: ' + last_seen);
      console.log('seen_count: ' + seen_count);

      segment.application_metadata = { first_seen: first_seen, last_seen: last_seen, seen_count: seen_count };

      console.log('attempting to save segment: ' + segment);

      collection.update({startTime: segment.startTime}, segment, {upsert:true, w: 1}, function(err, result)
      {
        if (err) { throw err; }
        // collection.insert(segment, {upsert:true, w: 1}, function(err, result) {

        console.log("saved segment, result.result:");
        console.log(result.result);
        wrote_segment_count++;
        cleanup_db_connection(db);
      });
    });
  });
}

function save_activity(db,activity) {

  var collection = db.collection("activities");

  collection.find({ startTime: activity.startTime}, function(err, cursor)
  {
    if (err) { throw err; }

    console.log("activity.startTime: " + activity.startTime);

    console.log('calling find() on activities');

    var first_seen;
    var seen_count;

    cursor.toArray(function(err, result)
    {
      if (err) { throw err; }

      console.log('result.length: ' + result.length);

      if(result.length === 0)
      {
        first_seen = now;
        seen_count = 1;
      }
      else if(result.length === 1)
      {
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
      }
      else
      {
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
        throw("too many results!");
      }

      console.log('first_seen: ' + first_seen);
      console.log('last_seen: ' + last_seen);
      console.log('seen_count: ' + seen_count);

      activity.application_metadata = { first_seen: first_seen, last_seen: last_seen, seen_count: seen_count };

      console.log('attempting to save activity: ' + activity);

      collection.update({startTime: activity.startTime}, activity, {upsert:true, w: 1}, function(err, result)
      {
        if (err) { throw err; }
        // collection.insert(activity, {upsert:true, w: 1}, function(err, result) {
        console.log("saved activity, result.result:");
        console.log(result.result);
        wrote_activity_count++;
        cleanup_db_connection(db);
      });
    });
  });
}



process.stdin.on('end', function() {
  var incoming_string = stdin_chunks.join("");
  var url;
  incoming_json = JSON.parse(incoming_string);

  if(incoming_json.length === 0 || incoming_json.length === undefined) {
    throw "Invalid json: " + incoming_string;
  }


  // connect to db and store data
  //

  MongoClient.connect(dburl, function(err, db)
  {
    var i, date;
    if (err) { throw err; }
    function process_api_response (error, response, body) {
      if(error) { throw error; }
      if(response.statusCode !== 200) {
        throw "Response status not 200 (" + response.statusCode + "), body: " + body;
      }
      var j;
      var segment;
      var segments;
      var activity;
      var activities;
      var storyline;
      var k;
      if (!error && response.statusCode === 200) {
        storyline = JSON.parse(body)[0];

        segments = storyline.segments;
        console.log('segments.length: ' + segments.length);

        if(!segments) { segments = []; }

          for(j = 0 ; j < segments.length ; j++)
          {
            total_segment_count++;
            segment = segments[j];
            save_segment(db, segment);

            activities = segment.activities;

            if(!activities) { activities = []; }

            for(k = 0 ; k < activities.length ; k++)
            {
              total_activity_count++;
              activity = activities[k];
              save_activity(db, activity);
            }
           }
      }
    }


    console.log("incoming_json.length: " + incoming_json.length);

    // one item per day
    //

    for(i = 0 ; i < incoming_json.length; i++) {

      date = incoming_json[i];

      save_date(db,date);
      total_date_count++;


      url = 'https://api.moves-app.com/api/1.1/user/storyline/daily/' + date.date + '?trackPoints=true&access_token=' + moves_access_token;
      console.log("requesting " + url);
      request(url, process_api_response);


      }
  });
});




