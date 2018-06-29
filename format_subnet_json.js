#!/usr/bin/env node
// Format aws ec2 describe-subnets output into csv data - name, id, etc...
//
// Example usage:
// aws ec2 describe-subnets | ./format_subnet_json.js
//

var stdin_chunks = []
var stdout_chunks = []

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});

// tags to include in output (case insensitive) (actual ec2 tags)
//
var output_tags = [ "Name" ]

// json fields to include in output (case sensitive) (not tags, standard ec2 metadata)
//
var output_fields = [ "SubnetId", "AvailabilityZone", "State", "VpcId", "MapPublicIpOnLaunch", "CidrBlock" ]

process.stdin.on('end', function() {

  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);

  incoming_json.Subnets.forEach(function(subnet) {

        var subnet_tags = {};
        if(!subnet.Tags) { subnet.Tags = [] }

        subnet.Tags.forEach(function(tag) {
          output_tags.forEach(function(output_tag) {
            output_tag = output_tag.toLowerCase();
            if(tag.Key.toLowerCase() === output_tag) {
              subnet_tags[output_tag] = tag.Value;
            }
          });
        });


    // to track whether to print a comma
    //
    var printed_field = false;

    output_fields.forEach(function(output_field) {
      if(!subnet[output_field]) { subnet[output_field] = ''; }
      if(printed_field) {
        stdout_chunks[stdout_chunks.length] = ","
      }
      stdout_chunks[stdout_chunks.length] = subnet[output_field]
      printed_field = true;
    });

    output_tags.forEach(function(output_tag) {
      output_tag = output_tag.toLowerCase();
      if(!subnet_tags[output_tag]) { subnet_tags[output_tag] = ''; }
      stdout_chunks[stdout_chunks.length] = ","
      stdout_chunks[stdout_chunks.length] = subnet_tags[output_tag]
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

output_tags.forEach(function(output_tag) {
  process.stdout.write(",");
  process.stdout.write(output_tag);
});


process.stdout.write("\n");

var signals = ['SIGINT', 'SIGPIPE','SIGHUP','SIGTERM' ]
for(var i = 0 ; i < signals.length ; i++) {
  process.on(signals[i], function() {
    console.log('Got ' + signal);
  });
}
