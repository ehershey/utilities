#!/bin/sh
i=2000 
if [ "$1" ]
then
  export recip="$1"
else
  export recip=ernie.hershey@10gen.com
fi
while true 
do 
   date=`date`
 echo $i 
 echo $date
 (echo test $i 
 date ) | mail -s "test $i" $recip
  i=`expr $i + 1`
 sleep 5 
done
