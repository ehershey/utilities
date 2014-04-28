#!/bin/bash
PATH=$PATH:$(dirname $0)
dumpimapjson.js | mongoimport --db erniemail --collection messages --drop
echo 'db.messages.aggregate( [ { $group: { _id: "$headers.from", count: { "$sum": 1 } } } , { $sort: { count: 1 } }, { $unwind: "$_id" }] ).forEach(function(item) { print(item.count + ": " + item._id) }) ' | mongo erniemail | tail | ( echo ; cat | cut -f2 -d: | sed 's/.*<\(.*\)>/\1/g'  | sed 's/$/ OR /g' | tr -d \\n ; echo ) | sed 's/ OR bye *OR *$//' 
