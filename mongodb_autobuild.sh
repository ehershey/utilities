#!/bin/sh
# Automatically build MongoDB every night
#
#

BUILD_DIR=/Users/ernie/git/mongo.autobuild
REV=master
SCONS_ARGS="-j8 --ssl all" 

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
eval scons $SCONS_ARGS
