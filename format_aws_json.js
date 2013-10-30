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

process.stdin.on('end', function() {
  var incoming_string = stdin_chunks.join("");
  var incoming_json = JSON.parse(incoming_string);

  incoming_json.Reservations.forEach(function(reservation) { 
      reservation.Instances.forEach(function(instance) { 

        var instance_name = '';
        instance.Tags.forEach(function(tag) { 
          if(tag.Key === "Name")
          {
            instance_name = tag.Value;
          }
        });
        process.stdout.write(instance_name);
        process.stdout.write(",");
        process.stdout.write(instance.PublicDnsName);
        process.stdout.write("\n");
      });
  });
});
