#!/usr/bin/env node
// Format aws ec2 describe-instances output into csv data - instance_name, dns_name
//
// Example usage:
// aws ec2 describe-instances --filters '[{"name":"tag:Name","values":["*test_rhel*"]}, { "name": "tag:username", "values": ["Ernie Hershey"]}]'    | ./format_aws_json.js
//
// aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" | ~/git/utilities/format_aws_json.js

// read json on stdin into memory
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
var output_fields = [ "State.Name", "InstanceId", "InstanceType", "KeyName", "PublicDnsName", "ImageId", "Placement.AvailabilityZone", "VpcId", "LaunchTime", "PublicIpAddress", "PrivateIpAddress" ]

process.stdin.on('end', function() {

  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);

  incoming_json.Reservations.forEach(function(reservation) {
      reservation.Instances.forEach(function(instance) {

        var instance_tags = {};
        if(!instance.Tags) { instance.Tags = [] }

        instance.Tags.forEach(function(tag) {
          output_tags.forEach(function(output_tag) {
            output_tag = output_tag.toLowerCase();
            if(tag.Key.toLowerCase() === output_tag) {
              instance_tags[output_tag] = tag.Value;
            }
          });
        });


        // to track whether to print a comma
        //
        var printed_field = false;

        output_fields.forEach(function(output_field) {
          if(!instance[output_field]) { instance[output_field] = ''; }
          if(printed_field) {
            stdout_chunks[stdout_chunks.length] = ","
          }

          // object to pull field directly from
          //
          var field_parent = instance;

          // pull different field parent out of field name (i.e. "Placement" out of "Placement.AvailabilityZone")
          //
          var field_parent_name = output_field.replace(/\..*/,'');
          if(field_parent_name != output_field)
          {
            field_parent = field_parent[field_parent_name];
            output_field = output_field.replace(/.*\./,'');
          }

          stdout_chunks[stdout_chunks.length] = field_parent[output_field]
          printed_field = true;
        });

        output_tags.forEach(function(output_tag) {
          output_tag = output_tag.toLowerCase();
          if(!instance_tags[output_tag]) { instance_tags[output_tag] = ''; }
          stdout_chunks[stdout_chunks.length] = ","
          stdout_chunks[stdout_chunks.length] = instance_tags[output_tag]
        });
        stdout_chunks[stdout_chunks.length] = "\n"
      });
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
  var signal = signals[i];
  process.on(signals[i], function() {
    console.log('Got ' + signal);
    if(signal === 'SIGTERM')
    {
      process.exit();
    }

  });
}
