#!/bin/bash -e
#
# Given a version of the MongoDB Server, verify push artifacts to 
# determine how many of the total files that need to wind up pushed have
# been pushed.

trap "echo ; echo ERROR!" err

version="$1"
if [ ! "$version" ] 
then
  echo "Usage: $0 <version>"
  exit 1
fi

all_files="
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-subscription-amzn64-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-subscription-rhel57-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-subscription-rhel62-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-subscription-suse11-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-subscription-ubuntu1204-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-i686-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-i686-debugsymbols-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-i686-rhel57-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-i686-static-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-debugsymbols-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-legacy-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-rhel57-%s.tgz
s3://downloads.mongodb.org/win32/mongodb-win32-i386-%s.zip
s3://downloads.mongodb.org/win32/mongodb-win32-x86_64-%s.zip
s3://downloads.mongodb.org/win32/mongodb-win32-x86_64-2008plus-%s.zip
s3://downloads.mongodb.org/osx/mongodb-osx-x86_64-%s.tgz
s3://downloads.mongodb.org/sunos5/mongodb-sunos5-x86_64-%s.tgz
"

for push_file_pattern in $all_files
do
  push_file=`printf $push_file_pattern $version`
  #echo push_file: $push_file
  echo -n .
  if ! aws s3 ls $push_file | grep `basename $push_file`$ >/dev/null 
  then
    echo
    echo "ERROR: missing file: $push_file"
  fi
done
echo
exit

tempdir=`mktemp -d /tmp/verify_versions.XXXXXX`

echo "tempdir: $tempdir"

cd $tempdir

cache_get 86400 http://downloads.mongodb.org/src/mongodb-src-r$version.tar.gz | tar zxf - 

echo checking version.cpp
grep 'const char versionString\[\] = "'$version'"' mongodb-src-r$version/src/mongo/util/version.cpp 
echo checking doxygenConfig
grep "PROJECT_NUMBER *= $version$" mongodb-src-r$version/doxygenConfig


filename=mongodb-osx-x86_64-$version.tgz
cache_get 86400 http://downloads.mongodb.org/osx/$filename | tar zxf - 

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

