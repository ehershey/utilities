#!/bin/bash

#mailto=devops@10gen.com
mailto=ernie.hershey@10gen.com

urls="
http://www.10gen.com/
http://corp.10gen.com/
http://www.mongodb.org/
http://docs.mongodb.org/
http://wiki.10gen.com/
"

tempfile_pattern=/tmp/temp_monitor.tempfile

for url in $urls
do
  safeurl="`echo \"$url\" | sed 's/[^a-zA-Z0-9]/_/g'`"
  tempfile=$tempfile_pattern-$safeurl
  tempfile_last=$tempfile_pattern-$safeurl.last
  curl --location --silent $url > $tempfile
  md5="`cat $tempfile| grep -vE 'theme_token|build_id|dom-id|atlassian-token|confluence-request-time' | md5`"
  if [ -e $tempfile_last ]
  then
    md5_last="`cat $tempfile_last| grep -vE 'theme_token|build_id|dom-id|atlassian-token|confluence-request-time' | md5`"

    if [ $md5 != $md5_last ]
    then
      subject="CONTENT DIFFERENCE DETECTED FOR URL $url"
      echo $subject
      mail_tempfile=`mktemp $tempfile_patterh.XXXXX`
      echo -n > $mail_tempfile
      echo -e "\n\n\ncontent diff:\n\n\n" >> $mail_tempfile
      diff $tempfile_last $tempfile >> $mail_tempfile
      echo -e "\n\n\nlatest content:\n\n\n" >> $mail_tempfile
      cat $tempfile >> $mail_tempfile
      echo -e "\n\n\nprevious content:\n\n\n" >> $mail_tempfile
      cat $tempfile_last >> $mail_tempfile
      echo -e "EOM" >> $mail_tempfile
      cat $mail_tempfile
      mail -s "$subject" $mailto < $mail_tempfile
    fi
  fi

  echo $url: $md5 / $md5_last
  mv $tempfile $tempfile_last
done
