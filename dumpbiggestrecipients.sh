#!/bin/bash
PATH=$PATH:$(dirname $0)
cache_run 600 dumpimapjson.js | mongoimport --db erniemail --collection messages --drop
echo 'db.messages.aggregate( [ { $group: { _id: "$headers.to", count: { "$sum": 1 } } } , { $sort: { count: 1 } }, { $unwind: "$_id" }] ).forEach(function(item) { print(item.count + ": " + item._id) }) ' | mongo erniemail 
