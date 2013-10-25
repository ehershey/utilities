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

env['use_ssh_config'] = True
env['key_filename'] = "/Users/ernie/git/ops-private/ec2/aws-build/admin1.pem"


expected_version = "2.4.3"

def hello():
      print("Hello world!")
      run("hostname")


def setuprepo():

    if env.pre_repo_cmd is not None:
      sudo(env.pre_repo_cmd)

    run("echo '%s' | sudo tee %s " % (env.repo_String, env.repo_file))

    if env.post_repo_cmd is not None:
      sudo(env.post_repo_cmd)


def installpackage():
    sudo(env.install_cmd % env.packages)

def verifypackage():
  verifymongodrunning()

def verifymongodnotrunning():
  assert(False == is_mongod_running), "Mongod running";

def verifymongodrunning():
  assert(True == is_mongod_running), "Mongod not running";

def verifyversion():
    output = run("echo 'db.serverBuildInfo().version' | mongo --quiet")

    fabric.utils.puts("expected version number:")
    fabric.utils.puts(expected_version)

    assert (output == expected_version), "Returned version not equal to expected version"

def uninstallpackage():
    sudo(env.uninstall_cmd % env.packages)

def start_mongod():
    sudo("service %s start" % env.init_service_name)

def stop_mongod():
    sudo("service %s stop" % env.init_service_name)

def is_mongod_running():
    output = run("pidof mongod", quiet = True)
    if output.return_code == 0:
      return True
    else:
      return False


