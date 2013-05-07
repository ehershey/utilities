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
# ami_id = 'ami-8568efec'
# region = 'us-east-1'
# key_name = 'admin1'
# security_group = 'default'
# instance_type = 'm1.large'

# rhel 6.4
#
ami_id = 'ami-f6f16b9f'
region = 'us-east-1'
key_name = 'admin1'
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
  security_groups=[security_group])

timeout = 60

inst = res.instances[0]

start_time = datetime.datetime.now()
timestamp_string = start_time.strftime("%Y%m%d%H%M%S")
instance_name = "package-test-%s" % timestamp_string

inst.add_tag("Name",instance_name)
inst.update()

print "instance name: %s" % instance_name
print "instance state: %s" % inst.state


elapsed_seconds = (datetime.datetime.now() - start_time).seconds

while inst.state == 'pending' and elapsed_seconds <= timeout:
  time.sleep(2)
  inst.update()
  print "instance state: %s" % inst.state
  elapsed_seconds = (datetime.datetime.now() - start_time).seconds

print "%d seconds elapsed" % elapsed_seconds
if inst.state != 'running':
  print "Unknown instance state: %s" % inst.state
print "connecting..."
print "dns name: " % inst.dns_name

