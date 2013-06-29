#!/usr/bin/python
import boto.ec2
import datetime
from fabric.api import execute, env
from fabfile import  setuprepo, installpackage, verifypackage, uninstallpackage, start_mongod, stop_mongod, verifymongodrunning, verifymongodnotrunning
import os
import time

env.timeout = 60
env.connection_attempts = 5


# parms for ec2 instance
#
# debian squeeze 
#
# label = 'debian squeeze'
# ami_id = 'ami-8568efec'
# region = 'us-east-1'
# key_name = 'admin1'
# security_group = 'default'
# instance_type = 'm1.large'
#

# centos 5.4
#
label = 'centos 54'
ami_id = 'ami-ccb35ea5'

# centos 5.4 32 bit
#
label = 'centos 56 32'
ami_id = 'ami-3f854656'

# centos 5.4 64 bit
#
label = 'centos 56 64'
ami_id = 'ami-7385461a'





#http://aws.amazon.com/solutions/global-solution-providers/redhat/

# rhel 6.4
#
label = 'rhel 64' 
ami_id = 'ami-f6f16b9f' 
env['user'] = 'ec2-user'

# rhel 5.7
#
label = 'rhel 57' 
ami_id = 'ami-83573eea'
env['user'] = 'root'

# rhel 5.8 
label = 'rhel 58'
ami_id = 'ami-a3563fca'
env['user'] = 'root'

# rhel 5.9 
label = 'rhel 59'
ami_id = 'ami-cf5b32a6'
env['user'] = 'root'

# rhel 6.2
#
label = 'rhel 62' 
ami_id = 'ami-876c05ee' 
env['user'] = 'root'




# debian squeeze
#
#label = 'debian squeeze' 
#ami_id = 'ami-8568efec' 
#env['user'] = 'admin'

# ubuntu 12.04
#
#label = 'ubuntu 12.04' 
#ami_id = 'ami-3fec7956'
#env['user'] = 'ec2-user'



region = 'us-east-1'
key_name = 'admin1'
security_group = 'default'
instance_type = 'm1.large'

# start redhat config
#
env.init_script_name = "mongod"
env.init_service_name = "mongod"
env.pre_repo_cmd = None
env.repo_String = """[10gen] 
name=10gen Repository 
#baseurl=http://temp-ubuntu1204-7.10gen.cc/downloads-distro.mongodb.org/repo/redhat/os/x86_64 
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64 
gpgcheck=0 
enabled=1"""
env.repo_file = "/etc/yum.repos.d/10gen.repo"
env.post_repo_cmd = "yum --quiet makecache"
env.packages="mongo-10gen-unstable mongo-10gen-unstable-server"
# full commands to install/uninstall env.packages with string replaced by env.packages setting above
#
env.install_cmd = "yum install --assumeyes --quiet %s"
env.uninstall_cmd = "yum --assumeyes --quiet remove %s"

# end redhat config

# start debian config
#
env['user'] = 'admin'
env.init_script_name = "mongodb"
env.init_service_name = "mongodb"
env.pre_repo_cmd = "apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10"
#env.repo_String = "deb http://temp-ubuntu1204-7.10gen.cc/downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen"
env.repo_String = "deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen"
env.repo_file = "/etc/apt/sources.list.d/10gen.list"
env.post_repo_cmd = "apt-get --yes --quiet update"
env.packages="mongodb-10gen-unstable"
# full commands to install/uninstall env.packages with string replaced by env.packages setting above
#
env.install_cmd = "apt-get --yes --quiet install %s"
env.uninstall_cmd = "apt-get --yes --quiet purge %s"

# end debian config






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
instance_name = "pkg-tst-%s-%s" % (label.replace(" ","_"), timestamp_string)

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
print "dns name: %s " % inst.dns_name

env.hosts = [ inst.dns_name ]

execute(verifymongodnotrunning)
execute(setuprepo)
execute(installpackage)
execute(verifymongodrunning)
env.packages = "numactl"
execute(installpackage)
execute(stop_mongod)
execute(verifymongodnotrunning)
execute(start_mongod)
execute(verifymongodrunning)
