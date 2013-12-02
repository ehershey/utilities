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

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});

// tags to include in output (case insensitive) (actual ec2 tags)
//
var output_tags = [ "Name", "Username", "Hostname", "started_by", "distro" ];

// json fields to include in output (case sensitive) (not tags, standard ec2 metadata)
var output_fields = [ "StateName", "InstanceId", "InstanceType", "KeyName", "PublicDnsName" ]

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

        // set StateName field to State.Name
        //
        instance.StateName = instance.State.Name;

        // to track whether to print a comma
        // 
        var printed_field = false; 

        output_fields.forEach(function(output_field) { 
          if(!instance[output_field]) { instance[output_field] = ''; }
          if(printed_field) {
            process.stdout.write(",");
          }
          process.stdout.write(instance[output_field]);
          printed_field = true;
        });

        output_tags.forEach(function(output_tag) { 
          output_tag = output_tag.toLowerCase();
          if(!instance_tags[output_tag]) { instance_tags[output_tag] = ''; }
          process.stdout.write(",");
          process.stdout.write(instance_tags[output_tag]);
        });
        process.stdout.write("\n");
      });
  });
});
