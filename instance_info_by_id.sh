#!/bin/sh
id="$1"
if [ ! "$id" ] 
then
  echo "usage: $0 <instance id>"
  exit 2
fi

if [ ! "`echo $id | grep ^i-`" ]
then
  id="i-$id"
fi
echo "Searching for id: $id"
aws ec2 describe-instances --filters '[{"Name":"instance-id","Values":["'$id'"]}]' | `dirname $0`/format_aws_json.js
