#!/bin/bash
i=2000 
if [ "$1" ]
then
  export recip="$1"
else
  export recip=pebble@ernie.org
fi
while true 
do 
   date=`date`
 echo $i 
 echo $date
 (echo test $i 
 date ) | mail -s "test $i at $date" $recip
  let i=i+1 
 sleep 5 
done
