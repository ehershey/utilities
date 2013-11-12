#!/usr/bin/node
// Format aws ec2 describe-instances output into csv data - instance_name, dns_name
//
// Example usage:
// aws ec2 describe-instances --filters '[{"name":"tag:Name","values":["*test_rhel*"]}, { "name": "tag:username", "values": ["Ernie Hershey"]}]'    | ./format_aws_json.js 

// read json on stdin into memory
//

var stdin_chunks = []

process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function(chunk) {
  stdin_chunks.push(chunk);
});

// tags to include in output
//
var output_tags = [ "Name", "Username" ];

process.stdin.on('end', function() {
  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);

  incoming_json.Reservations.forEach(function(reservation) { 
      reservation.Instances.forEach(function(instance) { 

        var instance_tags = {};
        if(!instance.Tags) { instance.Tags = [] }

        instance.Tags.forEach(function(tag) { 
          output_tags.forEach(function(output_tag) { 
            if(tag.Key === output_tag) {
              instance_tags[output_tag] = tag.Value;
            }
          });
        });

        output_tags.forEach(function(output_tag) { 
          if(!instance_tags[output_tag]) { instance_tags[output_tag] = ''; }
          process.stdout.write(instance_tags[output_tag]);
          process.stdout.write(",");
        });
        if(!instance.PublicDnsName) { instance.PublicDnsName = ''; } 
        process.stdout.write(instance.PublicDnsName);
        process.stdout.write("\n");
      });
  });
});
