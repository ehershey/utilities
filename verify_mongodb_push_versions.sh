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

if [ ! "$AWS_SECRET_ACCESS_KEY" -o ! "$AWS_ACCESS_KEY_ID" ]
then
  . ~/amazon-nocadmin.sh
fi

# Filenames contain "subscription" for 2.4 and older and "enterprise" for
# newer versions.
if echo "$version" | grep -q 2.4
then
  enterprise_name="subscription"
else
  enterprise_name="enterprise"
fi

all_files="
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-$enterprise_name-amzn64-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-$enterprise_name-rhel57-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-$enterprise_name-rhel62-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-$enterprise_name-suse11-%s.tgz
s3://downloads.10gen.com/linux/mongodb-linux-x86_64-$enterprise_name-ubuntu1204-%s.tgz
s3://downloads.10gen.com/win32/mongodb-win32-x86_64-$enterprise_name-windows-64-%s.msi
s3://downloads.mongodb.org/linux/mongodb-linux-i686-%s.tgz
s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-%s.tgz
s3://downloads.mongodb.org/win32/mongodb-win32-i386-%s.zip
s3://downloads.mongodb.org/win32/mongodb-win32-x86_64-%s.zip
s3://downloads.mongodb.org/win32/mongodb-win32-x86_64-2008plus-%s.zip
s3://downloads.mongodb.org/osx/mongodb-osx-x86_64-%s.tgz
s3://downloads.mongodb.org/sunos5/mongodb-sunos5-x86_64-%s.tgz
"
# s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-legacy-%s.tgz
# s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-rhel57-%s.tgz
# s3://downloads.mongodb.org/linux/mongodb-linux-i686-rhel57-%s.tgz
# s3://downloads.mongodb.org/linux/mongodb-linux-i686-static-%s.tgz
# s3://downloads.mongodb.org/linux/mongodb-linux-i686-debugsymbols-%s.tgz
# s3://downloads.mongodb.org/linux/mongodb-linux-x86_64-debugsymbols-%s.tgz

tried=0
found=0

for push_file_pattern in $all_files
do
  tried=`expr $tried + 1`
  push_file=`printf $push_file_pattern $version`
  if ! aws s3 ls $push_file | grep `basename $push_file`$ >/dev/null 
  then
    echo "ERROR: $push_file"
  else
    echo "FOUND: $push_file"
    found=`expr $found + 1`
  fi
done
echo
echo "Found $found/$tried"
