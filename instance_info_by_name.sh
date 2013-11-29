#!/bin/sh
name="$1"
if [ ! "$name" ] 
then
  echo "usage: $0 <instance name (or pattern - i.e. pkg_test_linux-64-large_20131129*>"
  exit 2
fi

aws ec2 describe-instances --filters "Name=tag:Name,Values=$name" | `dirname $0`/format_aws_json.js
