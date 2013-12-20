#!/usr/bin/env python

import boto.ec2
import datetime
from fabfile import install_package_building_prereqs, clone_mongodb_repo
from fabric.api import execute, env
import os
import settings
import time

USERNAME = os.environ['USER']


env.timeout = 60
env.connection_attempts = 5

region = 'us-east-1'
key_name = 'admin1'
env.key_filename = '/Users/ernie/.ssh/admin1.pem'
security_group = 'default'
instance_type = 'm1.large'

# ubuntu 12.04
#
label = 'ubuntu 12.04' 
ami_id = 'ami-3fec7956'
env['user'] = 'ubuntu'




AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
if not AWS_ACCESS_KEY_ID:
  print "required settings export missing: AWS_ACCESS_KEY_ID:"
  exit(2)

AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
if not AWS_SECRET_ACCESS_KEY:
  print "required settings export missing: AWS_SECRET_ACCESS_KEY:"
  exit(2)

os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY

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
instance_name = "pkg-tst-%s-%s" % (label.replace(" ", "_"), timestamp_string)

inst.add_tag("Name", instance_name)
inst.add_tag("Username", USERNAME)
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
print "dns name: %s " % inst.dns_name

# TODO actually check for availability
time.sleep(5)

elapsed_seconds = (datetime.datetime.now() - start_time).seconds

print "%d seconds elapsed" % elapsed_seconds

env.hosts = [inst.dns_name]

execute(install_package_building_prereqs)
execute(clone_mongodb_repo)
execute(packager_py)

# done - spin up ubuntu machine 
# install pre-req packages
# install gpg key
# done - clone repo
# tag repo
# run packager.py 
# copy repo into place
# run packager-enterprise.py into /tmp
# copy repo into place
# iterate through distros running all tests

