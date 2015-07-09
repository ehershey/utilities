#!/usr/bin/python
#
# Display Evergreen patches and patch info
#
# Usage:
# show_patches.py [ --verbose ]
#
# --verbose includes extra information like the URL being requested
#

import argparse
import requests
import sys

URL = 'https://evergreen.mongodb.com/json/patches/user/ernie.hershey%4010gen.com?page=0'


def main():
    parser = argparse.ArgumentParser(description='Show Patches')
    parser.add_argument('--verbose','-v', default = False, action='store_true', help='Display info about processing');
    args = parser.parse_args()

    url = URL

    if args.verbose:
        print("Requesting %s" % url)

    response = requests.get(url)

    data = response.json()

    print "Status, Time, Project, Base, Description"
    for patch in data['UIPatches']:
      patch=patch['Patch']
      if patch['Activated']:
        status = "Activated"
      else:
        status = "Inactive"
      print("%s, %s, %s, %s, %s" % (status, patch['CreateTime'], patch['Project'], patch['Githash'], patch['Description']))
    exit()
main()
