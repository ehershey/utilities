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

tempfile=$(mktemp /tmp/create_snapshot.XXXXXX)

for instance_id in $(aws ec2 describe-instances --filter "Name=tag:Name,Values=$namefilter" --output text --query "Reservations[*].Instances[*].InstanceId")
do
      #attachment.instance-id
      instance_name=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$instance_id" "Name=key,Values=Name" | grep '"Value": "' | cut -f4 -d\")
      for volume_id in $(aws ec2 describe-volumes --filter "Name=attachment.instance-id,Values=$instance_id"  --query "Volumes[*].VolumeId" --output text)
      do
        script=$(basename $0)
        user="$USER"
        host=$(hostname)
        description="Created with $script by $user on host $host for ec2 instance $instance_id"
        aws ec2 create-snapshot --volume-id $volume_id --description "$description" | tee "$tempfile"

        snapshot_id=$(grep '"SnapshotId": "snap-' "$tempfile" | cut -f4 -d\")
        device_name=$(aws ec2 describe-volumes --volume-id $volume_id --query 'Volumes[*].Attachments[*].Device'   --output text)
        echo "snapshot_id: $snapshot_id"
        echo "instance_name: $instance_name"
        echo "device_name: $device_name"
        aws ec2 create-tags --resources $snapshot_id --tags Key=Name,Value="$instance_name $device_name"
      done
done

rm "$tempfile"
