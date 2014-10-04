# Fabric tasks for setting up a custom repo in redhat, centos, fedora, debian, or ubuntu,
# installing mongodb package and verifying the state of the system after installing it
#
# usage:
#
# fab setuprepo installpackage verifypackage uninstallpackage
#
#
from fabric.api import env, run, sudo, put, cd
import fabric.utils

env['use_ssh_config'] = True
env['key_filename'] = "/Users/ernie/git/ops-private/ec2/aws-build/admin1.pem"

# where to build packages
WORKDIR="/mnt/mongo"

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
  assert(False == is_mongod_running()), "Mongod running";

def verifymongodrunning():
  assert(True == is_mongod_running()), "Mongod not running";

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

def install_github_hostkey():
    run("echo 'github.com,207.97.227.239 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==' >> .ssh/known_hosts")
    run("sort -u -o .ssh/known_hosts .ssh/known_hosts")

def install_package_building_prereqs():
    sudo("apt-get --assume-yes update")
    sudo("apt-get install --assume-yes dpkg-dev rpm debhelper createrepo git lib32stdc++6 apache2 libsasl2-2 libssl1.0.0 libsnmp30 xfsprogs mailutils")
    sudo("chown ubuntu /var/www")

def clean_workdir():
    run("rm -rf %s" % WORKDIR)

def clone_mongodb_repo():
    install_github_hostkey()
    clean_workdir()
    server_repo = env['server_repo']
    server_repo_branch = env['server_repo_branch']
    run("git clone %s %s --branch %s" % (server_repo, WORKDIR, server_repo_branch))

def packager_py():
    version = env['package_version_to_build']
    suffix = env['package_suffix']
    branch = "local-community-v%s" % version
    tag = "r%s" % version
    with cd(WORKDIR):
      run("git checkout -b %s" % branch)
      run("perl -i -p -e 's/Version: .*/Version: %s/' /mnt/mongo/rpm/*.spec" % version)
      run("git commit -m 'version bump for community packages version %s' rpm/*.spec --allow-empty" % version)
      run("git tag %s -f" % tag)
      with cd("buildscripts"):
        run("python packager.py %s:%s" % (version, suffix) )

def packager_enterprise_py():
    version = env['package_version_to_build']
    suffix = env['package_suffix']
    branch = "local-enterprise-v%s" % version
    tag = "r%s" % version
    with cd(WORKDIR):
      run("git checkout -b %s" % branch)
      run("perl -i -p -e 's/Version: .*/Version: %s/' /mnt/mongo/rpm/*.spec" % version)
      run("git commit -m 'version bump for enterprise packages version %s' rpm/*.spec --allow-empty" % version)
      run("git tag %s -f" % tag)
      with cd("buildscripts"):
        run("python packager-enterprise.py %s:%s" % (version, suffix) )


def install_gpg_key():
    put("gpgexport")
    run("rm -rf .gnupg")
    run("gpg --import < gpgexport")

def mount_drive():
    sudo("umount /dev/xvdb");
    sudo("mkfs.xfs -f /dev/xvdb");
    sudo("mount /dev/xvdb");
    sudo("chown ubuntu /mnt")
