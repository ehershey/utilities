#!/usr/bin/python
#
# print out keys present in english translations file but not in pt-br translation
#

import json

filename="/tmp/trans.json"

trans = json.load(open(filename))


def get_missing_keys(obj, obj2):
  missing_keys = {}
  for key in obj:
        val = obj[key]
        if not key in obj2:
          if isinstance(val, str) or isinstance(val, unicode):
            missing_keys[key] = val
          elif isinstance(val, list):
            missing_keys[key] = "[list]"
          elif isinstance(val, dict):
            missing_sub_keys = get_missing_keys(val, {})
            for missing_sub_key in missing_sub_keys:
                missing_keys[key + '.' + missing_sub_key] = missing_sub_keys[missing_sub_key]
          else: # what else can it be??
            print("unknown object type: " + val.__class__.__name__)
        elif isinstance(obj[key], dict):
            missing_sub_keys = get_missing_keys(obj[key], obj2[key])
            for missing_sub_key in missing_sub_keys:
                missing_keys[key + '.' + missing_sub_key] = missing_sub_keys[missing_sub_key]
        elif isinstance(obj[key], list):
            missing_keys[key] = "[list]"
  return missing_keys

missing_keys = get_missing_keys(trans[0]['en'], trans[0]['pt-br'])
for missing_key in missing_keys:
  print "%s: (%s)" % (missing_key, missing_keys[missing_key])
