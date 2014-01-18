#!/bin/bash -ex
# create snapshots for every volume on every ec2 instance based on the instance name
#
# Requires the AWS CLI tools: http://aws.amazon.com/cli/
# 

# e.g. dev-apache-*.ernie.com
namefilter="$1"
if [ ! "$1" ]
then
  namefilter="*"
fi

for instance_id in $(aws ec2 describe-instances --filter "Name=tag:Name,Values=$namefilter" --output text --query "Reservations[*].Instances[*].InstanceId")
do
      #attachment.instance-id
      for volume_id in $(aws ec2 describe-volumes --filter "Name=attachment.instance-id,Values=$instance_id"  --query "Volumes[*].VolumeId" --output text)
      do
        aws ec2 create-snapshot --volume-id $volume_id
      done
done
