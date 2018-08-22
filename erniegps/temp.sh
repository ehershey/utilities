#!/bin/sh
set -o nounset
for i in 2018
 do  for j in 07 08
 do for k in $(seq -w 01 31)
 do 
   file=~/"Dropbox/Misc/Arc Export/$i-$j-$k.gpx"
   if test -e "$file"
 then 
   echo "$file"
   grep \<time "$file" | grep -v $i-$j-$k
 #else
   #echo "NO file: $file"
 fi
 done
 done
 done
