#!/usr/bin/env node
// Format ebs ec2 describe-volumes output into csv data - volume_name, size, type, etc...
//
// Example usage:
// ebs ec2 describe-volumes | ./format_ebs_json.js
//

var stdin_chunks = []
var stdout_chunks = []

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});

// json fields to include in output (case sensitive) (not tags, standard ec2 metadata)
//
var output_fields = [ "VolumeId", "Size", "State", "VolumeType", "AvailabilityZone" ]

process.stdin.on('end', function() {

  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);

  incoming_json.Volumes.forEach(function(volume) {

    // to track whether to print a comma
    //
    var printed_field = false;

    output_fields.forEach(function(output_field) {
      if(!volume[output_field]) { volume[output_field] = ''; }
      if(printed_field) {
        stdout_chunks[stdout_chunks.length] = ","
      }
      stdout_chunks[stdout_chunks.length] = volume[output_field]
      printed_field = true;
    });

    stdout_chunks[stdout_chunks.length] = "\n"
  });
  process.stdout.write(stdout_chunks.join(""));
});

// to track whether to print a comma
//
var printed_field = false;
output_fields.forEach(function(output_field) {
  if(printed_field) {
    process.stdout.write(",");
  }
  process.stdout.write(output_field);
  printed_field = true;
});

process.stdout.write("\n");

var signals = ['SIGINT', 'SIGPIPE','SIGHUP','SIGTERM' ]
for(var i = 0 ; i < signals.length ; i++) {
  process.on(signals[i], function() {
    console.log('Got ' + signal);
  });
}
