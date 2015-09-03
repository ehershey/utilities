#!/usr/bin/env python3

import argparse
import datetime
import os
import subprocess

DEFAULT_BASE = os.path.join(os.environ["HOME"], "Dropbox", "Documents")

parser = argparse.ArgumentParser(description='Make Journal Entry')
parser.add_argument('filename')
args = parser.parse_args()


if os.pathsep in args.filename:
    filename = args.filename
else:
    filename = os.path.join(DEFAULT_BASE, args.filename)

if "." not in filename:
    filename = filename + '.txt'

print(filename)

with open(filename, "a") as filehandle:
    filehandle.write(datetime.date.strftime(datetime.datetime.now(), "%D"))
    filehandle.write("\n")
    filehandle.write("\n")

editor = os.getenv('EDITOR', 'vi')
subprocess.call('%s %s' % (editor, filename), shell=True)
