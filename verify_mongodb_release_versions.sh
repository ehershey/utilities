#!/bin/bash
set -o errexit
set -o errtrace
trap "echo ERROR!" err

version="$1"
if [ ! "$version" ] 
then
  echo "Usage: $0 <version>"
  exit 1
fi

tempdir=`mktemp -d /tmp/verify_versions.XXXXXX`

echo "tempdir: $tempdir"

cd $tempdir

curl http://downloads.mongodb.org/src/mongodb-src-r$version.tar.gz | tar zxf - 

echo checking version.cpp
grep 'const char versionString\[\] = "'$version'"' mongodb-src-r$version/src/mongo/util/version.cpp 
echo checking doxygenConfig
grep "PROJECT_NUMBER *= $version$" mongodb-src-r$version/doxygenConfig


filename=mongodb-osx-x86_64-$version.tgz
curl http://downloads.mongodb.org/osx/$filename | tar zxf - 

while [ $port"0" -eq "0" -o $port"0" -le 10240 ]
do
    port=$RANDOM
  done

echo checking mongod --version:
./mongodb-osx-x86_64-$version/bin/mongod --version | tee /dev/tty | grep "db version v"$version
echo checking mongo shell --version:
./mongodb-osx-x86_64-$version/bin/mongo --version | tee /dev/tty | grep " "$version$

./mongodb-osx-x86_64-$version/bin/mongod --bind_ip 127.0.0.1 --port $port --syslog --fork --dbpath . --pidfilepath $tempdir/pid.txt
sleep 5
echo 'checking db.serverBuildInfo()' 

echo 'db.serverBuildInfo().version' | ./mongodb-osx-x86_64-$version/bin/mongo --port $port | grep -x $version

kill `cat $tempdir/pid.txt`
rm -rf $tempdir

echo ALL VERSIONS VERIFIED

