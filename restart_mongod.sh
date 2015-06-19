#!/bin/bash

# restart mongod service if it's not running
#
if ! /sbin/service mongod status
then
  /sbin/service mongod start
fi
