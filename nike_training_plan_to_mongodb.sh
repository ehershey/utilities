#!/bin/bash

DB=ernie_org
COLLECTION=training_plan


echo "db.$COLLECTION.ensureIndex({level: 1, day: 1}, { unique: true });" | mongo "$DB"

# 1, 2, or 3
# novice, intermediate, expert
#
for level in 1 2 3
do

  (echo day,distance,notes,level; cache_get 86400  "http://nikerunning.nike.com/nikeplus/v2/schedules/plus/marathon_${level}_en_us.xml" | sed 's/<\/Day>/#/g' | tr -d \\n | tr \# \\n | sed 's/ *<Day> */0/g' | sed "s/.*PlannedDistance value='//g" | sed "s/'.*='/#/g" | sed "s/'.*//g" | tr -d \\t | tr \# ,  | sed 's/\([0-9]\)$/\1,/' | grep -v ^\< | sed s/$/,$level/ | grep -n  '' | tr : ,    )|mongoimport --db "$DB" --collection "$COLLECTION" --type csv --headerline --upsertFields day,level
done
