#!/usr/bin/env python
# spin up packaging server, generate packages and test them
#
# Usage: test_packages [ --skip-community ] [ --skip-enterprise ] [ packaging server ]

import argparse
import boto.ec2
import datetime
from fabfile import install_package_building_prereqs, clone_mongodb_repo, packager_py, packager_enterprise_py, install_gpg_key
from fabric.api import execute, env
import os
import settings
import time

USERNAME = os.environ['USER']

# fabric options
#
env.timeout = 60
env.connection_attempts = 5

# aws options
region = 'us-east-1'
key_name = 'admin1'
env.key_filename = '/Users/ernie/.ssh/admin1.pem'
security_group = 'default'
instance_type = 'm1.large'

# ubuntu 12.04
#
label = 'ubuntu1204' 
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

# parse command line
#
parser = argparse.ArgumentParser(description='Test packages')
parser.add_argument('--skip-community', action='store_true', required=False, help='Skip community packages', default = False);
parser.add_argument('--skip-enterprise', action='store_true', required=False, help='Skip enterprise packages', default = False);
parser.add_argument('--server', help='Packaging serfver to use', default = None);

os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY

if sys.argv[1]:
  env.hosts = [sys.argv[1]]
else:
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
  instance_name = "pkg_test_%s_%s" % (label.replace(" ", "_"), timestamp_string)

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

# env['server_repo'] = 'git@github.com:mongodb/mongo'
# env['server_repo_branch'] = 'master'
env['server_repo'] = 'git@github.com:ehershey/mongo'
env['server_repo_branch'] = 'SERVER-9123-pkgtst'
execute(clone_mongodb_repo)

execute(install_gpg_key)

# need to figure out how to determine this version more dynamically
# 
env['package_version_to_build'] = '2.5.5'
env['package_suffix'] = '-org-unstable'
execute(packager_py)

# need to figure out how to determine this version more dynamically
# 
env['package_version_to_build'] = '2.5.5'
env['package_suffix'] = '-enterprise-unstable'
execute(packager_enterprise_py)




# done - spin up ubuntu machine 
# done install pre-req packages
# done install gpg key
# done - clone repo
# done tag repo
# done run packager.py 
# copy repo into place
# run packager-enterprise.py into /tmp
# copy repo into place
# iterate through distros running all tests

