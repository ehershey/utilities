#!/bin/bash
#
# Automatically build MongoDB every night
#
#
set -o verbose
set -o pipefail
set -o errexit
set -o nounset

if [ -e ~/.ssh-agent ] 
then
  . ~/.ssh-agent
fi

# Needed at least for sysctl
#
export PATH=$PATH:/usr/sbin

BUILD_DIR=/Users/ernie/git/mongo.autobuild
REV=master
#SCONS_ARGS="--use-new-tools all dist dist-debugsymbols distsrc-tgz --ssl --allocator=system -j$(sysctl -n hw.logicalcpu) --osx-version-min=10.7 --libc++ LINKFLAGS=-L/usr/local/opt/openssl/lib CCFLAGS=-I/usr/local/opt/openssl/include"
SCONS_ARGS="all --ssl --allocator=system -j$(sysctl -n hw.logicalcpu) --osx-version-min=10.7 --libc++ LINKFLAGS=-L/usr/local/opt/openssl/lib CCFLAGS=-I/usr/local/opt/openssl/include"
exe=
gorootvars=
gitvars=
tooltags="-tags 'ssl sasl'"
OS=osx


export PATH=$PATH:/usr/local/bin

for module in "$BUILD_DIR/src/mongo/db/modules/"*
do
  if [ -e "$module" ]
  then
    cd "$module"
    git fetch --all
    git reset --hard "origin/$REV"
  fi
done


cd "$BUILD_DIR"
git fetch --all
git reset --hard "origin/$REV"

# build tools
#

# create the target directory for the binaries
mkdir -p src/mongo-tools

# clone into a different path so the binaries and package directory
# names do not conflict
cd src/mongo-tools-repo
git fetch --all
git reset --hard "origin/$REV"

# make sure newlines in the scripts are handled correctly by windows
if [ "Windows_NT" = "$OS" ]; then
    set -o igncr
fi;

git checkout $REV
. ./set_gopath.sh

# In RHEL 5.5, /usr/bin/ld can't handle --build-id parameters, so
# use a wrapper if it's present on the system
#
if [ -d /opt/ldwrapper/bin ]
then
  export PATH=/opt/ldwrapper/bin:$PATH
fi

for i in bsondump mongostat mongofiles mongoexport mongoimport mongorestore mongodump mongotop mongooplog; do
     #eval ${gorootvars} go build -gccgoflags -I/usr/local/opt/openssl/include -ldflags \"-L/usr/local/opt/openssl/lib -X github.com/mongodb/mongo-tools/common/options.Gitspec $(git rev-parse HEAD) -X github.com/mongodb/mongo-tools/common/options.VersionStr $(git --git-dir ../../.git describe)\" ${tooltags} -o "../mongo-tools/$i${exe}" $i/main/$i.go
     echo $i;
done

cd "$BUILD_DIR"
find . -name \*.pyc -exec rm {} \;
echo scons $SCONS_ARGS >> autobuild-scons-cmd.txt
eval scons $SCONS_ARGS
