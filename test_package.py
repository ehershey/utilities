#!/usr/bin/python
import boto.ec2
import datetime
import os
import time

repo_base_url = 'http:#downloads-distro.mongodb.org/repo/'

# parms for ec2 instance
#
# debian squeeze 
#
ami_id = 'ami-8568efec'
region = 'us-east-1'
key_name = 'admin1';
security_group = 'default'
instance_type = 'm1.large'


AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID'] 
if not AWS_ACCESS_KEY_ID:
  print "required environment variable missing: AWS_ACCESS_KEY_ID:"
  exit(2)

AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY'] 
if not AWS_SECRET_ACCESS_KEY:
  print "required environment variable missing: AWS_SECRET_ACCESS_KEY:"
  exit(2)


conn = boto.ec2.connect_to_region(region)

res = conn.run_instances(
  ami_id,
  key_name = key_name,
  instance_type = instance_type,
  security_groups=[security_group]);

timeout = 60

inst = res.instances[0]

timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
instance_name = "package-test-%s" % timestamp;

inst.add_tag("Name",instance_name)
inst.update();

print "instance name: %s" % instance_name
print "instance state: %s" % inst.state

while inst.state == 'pending':
  time.sleep(2)
  inst.update()
  print "instance state: %s" % inst.state

if inst.state != 'running':
  print "Unknown instance state after %d seconds elapsed: %s" % (elapsed_seconds, inst.state)
print "connecting..."

