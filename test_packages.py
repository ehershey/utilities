#!/usr/bin/env python
# spin up packaging server, generate packages and test them
#
# Usage: test_packages [ --skip-community ] [ --skip-enterprise ] [ --server <packaging server> ] [ --server-repo <repo - e.g. git@github.com:mongodb/mongo> ] [ --server-repo-branch <branch> ] [ --skip-clone ] --version <version - e.g. 2.5.5>
#

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
parser.add_argument('--skip-clone', action='store_true', required=False, help='Skip cloning server repo', default = False);
parser.add_argument('--server-repo', help='Github repo to use', default = 'git@github.com:mongodb/mongo');
parser.add_argument('--server-repo-branch', help='Branch in repo to use', default = 'master');
parser.add_argument('--server', help='Packaging serfver to use', default = None);
parser.add_argument('--instance-type', help='Instance Type', default = 'm3.xlarge');
parser.add_argument('--version', help='Version number to build', required = True, default = None);
args = parser.parse_args()

os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY

if args.server:
  print("Using server %s\n" % args.server)
  env.hosts = [args.server]
else:
  print("Creating server\n")
  conn = boto.ec2.connect_to_region(region)
  bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping({'/dev/xvdb': 'ephemeral0', '/dev/xvdc': 'ephemeral1'})

  res = conn.run_instances(
    ami_id,
    key_name = key_name,
    instance_type = args.instance_type,
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
  execute(install_gpg_key)


if not args.skip_clone:
    # env['server_repo'] = 'git@github.com:mongodb/mongo'
    # env['server_repo_branch'] = 'master'
    # env['server_repo'] = 'git@github.com:ehershey/mongo'
    # env['server_repo_branch'] = 'SERVER-9123-pkgtst'
    env['server_repo'] = args.server_repo
    env['server_repo_branch'] = args.server_repo_branch
    execute(clone_mongodb_repo)


env['package_version_to_build'] = args.version

if not args.skip_community:
    env['package_suffix'] = '-org-unstable'
    execute(packager_py)

if not args.skip_enterprise:
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

