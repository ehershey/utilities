#!/bin/bash
#
# Rename an ec2 instance
# Usage: rename_instance.sh <old name> <new name>
#

old_name="$1"
new_name="$2"


if [ ! "$new_name" ]
then
  echo "usage: $0 <old name> <new name>"
  exit 1
fi

if [ ! "$AWS_SECRET_ACCESS_KEY" -o ! "$AWS_ACCESS_KEY_ID" ]
then
  . ~/amazon-build.sh
fi


instance_id=$(aws ec2 describe-instances --query Reservations[0].Instances[0].InstanceId --output text  --filters "Name=tag:Name,Values=$old_name")

if [ ! "$(echo $instance_id | grep ^i-)" ]
then
  echo "Can't find instance ID for instance named $old_name"
  exit 2
fi

echo aws ec2 create-tags --resources $instance_id  --tags "Key=Name,Value=$new_name"
aws ec2 create-tags --resources $instance_id  --tags "Key=Name,Value=$new_name"
