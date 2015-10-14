#!/bin/bash
export name="$1"
if [ ! "$name" ]
then
  echo "usage: $0 <instance name (or pattern - i.e. pkg_test_linux-64-large_20131129*>"
  exit 2
fi

if [ ! "$AWS_SECRET_ACCESS_KEY" -o ! "$AWS_ACCESS_KEY_ID" ]
then
  . ~/amazon-build.sh
fi

tempfile=`mktemp /tmp/awsXXXXXX`
aws ec2 describe-instances --filters "Name=tag:Name,Values=$name" > $tempfile
node `dirname $0`/format_aws_json.js < $tempfile
rm $tempfile
