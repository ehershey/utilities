#!/usr/bin/env node
// Format aws ec2 describe-images output into csv data - image_name, name, description
//
// Example usage:
// aws ec2 describe-images --owner self | ./format_aws_json.js
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
var output_fields = [ "State", "ImageId", "Name", "State", "Architecture", "OwnerId", "KernelId", "VirtualizationType" ]

process.stdin.on('end', function() {

  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);

  incoming_json.Images.forEach(function(image) {

    // to track whether to print a comma
    //
    var printed_field = false;

    output_fields.forEach(function(output_field) {
      if(!image[output_field]) { image[output_field] = ''; }
      if(printed_field) {
        stdout_chunks[stdout_chunks.length] = ","
      }
      stdout_chunks[stdout_chunks.length] = image[output_field]
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
