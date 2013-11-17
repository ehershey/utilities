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
// */5 * * * * curl --silent "https://api.moves-app.com/api/v1/user/activities/daily?pastDays=7&access_token=$MOVES_ACCESS_TOKEN"  | ~ernie/git/utilities/save_moves_activities.js > /tmp/save_moves_activities.log 2>&1


var mongodb = require('mongodb');
var request = require('request');

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

var MongoClient = mongodb.MongoClient
  , Server = mongodb.Server;

// var mongoClient = new MongoClient(new Server(dbserver, dbport));

// read json on stdin into memory
//

var stdin_chunks = []

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});


var now = new Date();

var last_seen = now;

var wrote_entry_count = 0;
var total_entry_count = 0;
var wrote_segment_count = 0;
var total_segment_count = 0;
var wrote_activity_count = 0;
var total_activity_count = 0;
var incoming_json;

process.stdin.on('end', function() {
  var incoming_string = stdin_chunks.join("");
  incoming_json = JSON.parse(incoming_string);


  // connect to db and store data
  //

  MongoClient.connect(dburl, function(err, db) 
  {
    if (err) throw err;

    console.log("incoming_json.length: " + incoming_json.length);
    
    for(var i = 0 ; i < incoming_json.length; i++) { 

      var entry = incoming_json[i];

      save_day_entry(db,entry);
      total_entry_count++;

      var segments = entry.segments;

      if(!segments) { segments = [] }

      for(var j = 0 ; j < segments.length ; j++) 
      {
        total_segment_count++;
        var segment = segments[j];
        save_segment(db, segment);

        var activities = segment.activities;

        for(var k = 0 ; k < activities.length ; k++) 
        {
          total_activity_count++;
          var activity = activities[k];
          save_activity(db, activity);
        }



      }
    }
  });
});

function save_day_entry(db,entry) 
{

  var collection = db.collection("dates");

  collection.find({ date: entry.date}, function(err, cursor) 
  {
    if (err) throw err;


    console.log("entry.date: " + entry.date);

    console.log('calling find() on dates');

    var first_seen;
    var seen_count;


    cursor.toArray(function(err, result)
    {
      if (err) throw err;
    

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
        throw("too many results!");
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
      } 

      console.log('first_seen: ' + first_seen);
      console.log('last_seen: ' + last_seen);
      console.log('seen_count: ' + seen_count);

      entry.application_metadata = { first_seen: first_seen, last_seen: last_seen, seen_count: seen_count };


      console.log('attempting to save entry: ' + entry);

      collection.update({date: entry.date}, entry, {upsert:true, w: 1}, function(err, result) 
      {
        if (err) throw err;
        // collection.insert(entry, {upsert:true, w: 1}, function(err, result) {

        console.log("saved entry");
        wrote_entry_count++;
        if(wrote_activity_count === total_activity_count && wrote_entry_count === total_entry_count && wrote_segment_count === total_segment_count) 
        {
          db.close();
        }

      });
    });
  });
}

function save_segment(db,segment) 
{

  var collection = db.collection("segments");

  collection.find({ startTime: segment.startTime}, function(err, cursor) 
  {
    if (err) throw err;

    console.log("segment.startTime: " + segment.startTime);

    console.log('calling find() on segments');

    var first_seen;
    var seen_count;

    cursor.toArray(function(err, result)
    {
      if (err) throw err;

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
        throw("too many results!");
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
      } 

      console.log('first_seen: ' + first_seen);
      console.log('last_seen: ' + last_seen);
      console.log('seen_count: ' + seen_count);

      segment.application_metadata = { first_seen: first_seen, last_seen: last_seen, seen_count: seen_count };

      console.log('attempting to save segment: ' + segment);

      collection.update({startTime: segment.startTime}, segment, {upsert:true, w: 1}, function(err, result) 
      {
        if (err) throw err;
        // collection.insert(segment, {upsert:true, w: 1}, function(err, result) {

        console.log("saved segment");
        wrote_segment_count++;
        if(wrote_activity_count === total_activity_count && wrote_entry_count === total_entry_count && wrote_segment_count === total_segment_count) 
        {
          db.close();
        }
      });
    });
  });
}

function save_activity(db,activity) 
{

  var collection = db.collection("activities");

  collection.find({ startTime: activity.startTime}, function(err, cursor) 
  {
    if (err) throw err;

    console.log("activity.startTime: " + activity.startTime);

    console.log('calling find() on activities');

    var first_seen;
    var seen_count;

    cursor.toArray(function(err, result)
    {
      if (err) throw err;

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
        throw("too many results!");
        console.log("result[0].application_metadata: ");
        console.log(result[0].application_metadata);
        first_seen = result[0].application_metadata.first_seen;
        seen_count = result[0].application_metadata.seen_count + 1;
      } 

      console.log('first_seen: ' + first_seen);
      console.log('last_seen: ' + last_seen);
      console.log('seen_count: ' + seen_count);

      activity.application_metadata = { first_seen: first_seen, last_seen: last_seen, seen_count: seen_count };

      console.log('attempting to save activity: ' + activity);

      collection.update({startTime: activity.startTime}, activity, {upsert:true, w: 1}, function(err, result) 
      {
        if (err) throw err;
        // collection.insert(activity, {upsert:true, w: 1}, function(err, result) {

        console.log("saved activity");
        wrote_activity_count++;
        if(wrote_activity_count === total_activity_count && wrote_entry_count === total_entry_count && wrote_segment_count === total_segment_count) 
        {
          db.close();
        }
      });
    });
  });
}
