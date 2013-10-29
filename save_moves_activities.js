// Save moves json on stdin to mongodb
//


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


var MongoClient = require('mongodb').MongoClient
  , Server = require('mongodb').Server;

var mongoClient = new MongoClient(new Server(dbserver, dbport));

// read json on stdin into memory
//

var stdin_chunks = []

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});

process.stdin.on('end', function() {
  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);


  // connect to db and store data
  //

  mongoClient.connect(dburl, function(err, db) {
    if(err) {
      console.log(err);
      process.exit(2);
    }
    if(!db) {
      console.log("No DB in connect callback");
      process.exit(3);
    }

    console.log("incoming_json.length: " + incoming_json.length);

    db.collection("moves_activity_dates", function(err, collection) {
      if(err) {
        console.log('err: ' + err);
        process.exit(2);
      }
      console.log("collection: " + collection);


      for(var i = 0 ; i < incoming_json.length; i++) { 

        var entry = incoming_json[i];

        console.log('attempting to save entry: ' + entry);

        console.log("entry.date: " + entry.date);

        collection.update({_id: entry.date}, entry, {upsert:true, w: 1}, function(err, result) {

          if(err) {
            console.log('err: ' + err);
            process.exit(2);
          }
          console.log("result: " + result);
          console.log("wrote entry: " + entry);
        });
      }
    });
        
  
    db.close();
  });
});
