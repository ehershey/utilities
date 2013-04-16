#!/usr/bin/python
import boto
import os

ami_id = 'ami-8568efec'
repo_base_url = 'http://downloads-distro.mongodb.org/repo/'


AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID'] 
if not AWS_ACCESS_KEY_ID:
  print "required environment variable missing: AWS_ACCESS_KEY_ID:"
  exit(2)

AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY'] 
if not AWS_SECRET_ACCESS_KEY:
  print "required environment variable missing: AWS_SECRET_ACCESS_KEY:"
  exit(2)



