#!/usr/bin/env python
#
# Run test_packages fabfile
#
from fabfile import  setuprepo, installpackage, verifypackage, uninstallpackage
from fabric.api import execute

execute(setuprepo)
execute(installpackage)
execute(verifypackage)
execute(uninstallpackage)
