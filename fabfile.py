# Fabric tasks for setting up a custom repo in redhat, centos, fedora, debian, or ubuntu, 
# installing mongodb package and verifying the state of the system after installing it
#
# usage:
#
# fab setuprepo installpackage verifypackage uninstallpackage
#
#
from fabric.api import env, run, sudo
import fabric.utils

# redhat
env['hosts'] = [ 'ec2-50-16-106-231.compute-1.amazonaws.com' ]
env['user'] = 'ec2-user'
init_script_name = "mongod"
init_service_name = "mongod"
pre_repo_cmd = None
repo_string = """[10gen] 
name=10gen Repository 
baseurl=http://temp-ubuntu1204-7.10gen.cc/downloads-distro.mongodb.org/repo/redhat/os/x86_64 
gpgcheck=0 
enabled=1"""
repo_file = "/etc/yum.repos.d/10gen.repo"
post_repo_cmd = "yum --quiet makecache"
packages="mongo-10gen-unstable mongo-10gen-unstable-server"
# full commands to install/uninstall packages with string replaced by packages setting above
#
install_cmd = "yum install --assumeyes --quiet %s"
uninstall_cmd = "yum --assumeyes --quiet remove %s"



# debian
#env['hosts'] = [ 'ec2-174-129-57-58.compute-1.amazonaws.com' ]
#env['user'] = 'admin'
#init_script_name = "mongodb"
#init_service_name = "mongodb"
#pre_repo_cmd = "apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10"
#repo_string = "deb http://temp-ubuntu1204-7.10gen.cc.downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen"
#repo_file = "/etc/apt/sources.list.d/10gen.list"
#post_repo_cmd = "apt-get --quiet --quiet --no-download update"
#packages="mongodb-10gen"
## full commands to install/uninstall packages with string replaced by packages setting above
##
#install_cmd = "apt-get --quiet --quiet install %s"
#uninstall_cmd = "apt-get --quiet --quiet purge %s"




env['use_ssh_config'] = True
env['key_filename'] = "/Users/ernie/git/ops-private/ec2/aws-build/admin1.pem"


expected_version = "2.4.3"

def hello():
      print("Hello world!")
      run("hostname")


def setuprepo():

    if pre_repo_cmd is not None:
      sudo(pre_repo_cmd)

    run("echo '%s' | sudo tee %s " % (repo_string, repo_file))

    if post_repo_cmd is not None:
      sudo(post_repo_cmd)


def installpackage():
    sudo(install_cmd % packages)

def verifypackage():
    run("ls -l /etc/init.d/%s" % init_script_name)

    if not is_mongod_running():
      start_mongod()

    run("ps auwx | grep -i mongo")

    output = run("echo 'db.serverBuildInfo().version' | mongo --quiet")

    fabric.utils.puts("expected version number:")
    fabric.utils.puts(expected_version)

    assert (output == expected_version),"Returned version not equal to expected version"

def uninstallpackage():
    sudo(uninstall_cmd % packages)

def start_mongod():
    sudo("service %s start" % init_service_name)

def stop_mongod():
    sudo("service %s stop" % init_service_name)

def is_mongod_running():
    output = run("pidof mongod", quiet = True)
    if output.return_code == 0:
      return True
    else:
      return False


