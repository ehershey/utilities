#!/bin/bash
# load crontab from crontab-workstation.txt
#
#
CRON_USER=ernie
FILEHOME=/Users/ernie/git/utilities
HOSTNAME_PATTERN1="imac"
HOSTNAME_PATTERN2="mba"
HOSTNAME_PATTERN3="mbp"
HOSTNAME_PATTERN4="mb12"
autoupdate_version = 6

if [ "$CRON_USER" != "$USER" ]
then
  command="sudo crontab -u $CRON_USER"
else
  command="crontab"
fi

if [ ! "`hostname -s | grep $HOSTNAME_PATTERN1`" -a ! "`hostname -s | grep $HOSTNAME_PATTERN2`" -a ! "`hostname -s | grep $HOSTNAME_PATTERN3`" -a ! "`hostname -s | grep $HOSTNAME_PATTERN4`" ]
then
  echo "Incorrect hostname: (looks like: $HOSTNAME, should contain: \"$HOSTNAME_PATTERN1\" or \"$HOSTNAME_PATTERN2\" or \"$HOSTNAME_PATTERN3\" or \"$HOSTNAME_PATTERN4\")"
  exit 3
fi


if [ ! -e "$FILEHOME/crontab-workstation.txt" ]
then
  echo "Can't find crontab-workstation.txt in $FILEHOME"
  exit 2
fi

if ! which -s ts
then
  # for "ts" command
  #
  brew install moreutils
fi


tempfile1=$(mktemp)
tempfile2=$(mktemp)

#cat "$FILEHOME/crontab-workstation.txt" | $command

crontab_file="$FILEHOME/crontab-workstation.txt"

# Save old crontab for comparison before overwriting
#
$command -l > $tempfile1

crontab_env_file="$FILEHOME/crontab.env"

echo -n > "$tempfile2"

if [ -e "$crontab_env_file" ]
then
  echo "# Below loaded from $crontab_env_file" >> "$tempfile2"
  echo "#" >> "$tempfile2"
  cat "$crontab_env_file" >> $tempfile2
fi


echo "" >> "$tempfile2"
echo "# Below loaded from $crontab_file" >> "$tempfile2"
echo "#" >> "$tempfile2"
cat "$crontab_file" >> $tempfile2

# Load machine specific addition if present
#
extra_file="$FILEHOME/crontab-workstation-$(hostname -s).txt"
if [ -e "$extra_file" ]
then
  echo >> "$tempfile2"
  echo "# Below loaded from $extra_file" >> "$tempfile2"
  echo "#" >> "$tempfile2"
  cat "$extra_file" >> "$tempfile2"
fi
if [[ ! "$(diff $tempfile1 $tempfile2)" ]]
then
  echo "No updates. Aborting."
  exit 1
fi
diff $tempfile1 $tempfile2
echo -n "Diff ok? (y/n): "
read ans
if [[ "$ans" == "y" ]]
then
  echo "Loading crontab."
  cat "$tempfile2" | $command
else
  echo Aborting.
fi

rm $tempfile1 $tempfile2
