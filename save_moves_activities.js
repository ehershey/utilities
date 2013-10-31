#!/usr/bin/node
'use strict';
// Save moves json on stdin to mongodb
//
// Entities: 
// 1) A day worth of activity
//    Collection: moves_activity_dates
//    Key: date
// 2) Segments
//    Collection: moves_activity_segments
//    Key: startTime
//
// For each entity, add fields:
// 1) application_metadata: { first_seen: <timestamp>, last_seen: <timestamp>, seen_count: <count> }


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

var MongoClient = require('mongodb').MongoClient
  , Server = require('mongodb').Server;

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

      for(var j = 0 ; j < segments.length ; j++) 
      {
        total_segment_count++;
        var segment = segments[i];
        save_segment(db, segment);
      }
    }
  });
});

function save_day_entry(db,entry) 
{

  var collection = db.collection("moves_activity_dates");

  collection.find({ date: entry.date}, function(err, cursor) 
  {
    if (err) throw err;


    console.log("entry.date: " + entry.date);

    console.log('calling find() on moves_activity_dates');

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

        console.log("result: " + result);
        console.log("entry: " + entry);
        wrote_entry_count++;
        if(wrote_segment_count === total_segment_count && wrote_entry_count === total_entry_count) 
        {
          db.close();
        }

      });
    });
  });
}

function save_segment(db,segment) 
{

  var collection = db.collection("moves_activity_segments");

  collection.find({ startTime: segment.startTime}, function(err, cursor) 
  {
    if (err) throw err;

    console.log("segment.startTime: " + segment.startTime);

    console.log('calling find() on moves_activity_segments');

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

        console.log("result: " + result);
        console.log("segment: " + segment);
        wrote_segment_count++;
        if(wrote_segment_count === total_segment_count && wrote_entry_count === total_entry_count) 
        {
          db.close();
        }
      });
    });
  });
}
