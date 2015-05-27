#!/usr/bin/python

import argparse
import requests
import sys

URL = 'https://evergreen.mongodb.com/json/timeline/mongodb-mongo-master?limit=1&skip=%s'


def main():
    parser = argparse.ArgumentParser(description='Build Status')
    parser.add_argument('--skip-commits','-s', default = 0, help='Commits to skip');
    args = parser.parse_args()

    skip = args.skip_commits

    response = requests.get(URL % skip)
    data = response.json()

    colorprint(bcolors.BOLD, "Build Variant,Status, Total, Success Count, Failed count")
    for version in data['Versions']:
        builds = version['Builds']
        for build in builds:
            line=""
            build = build['Build']
            line += build['display_name']
            line += ","
            build_status = ''
            tasks = build['tasks']
            success_count=0
            failed_count=0
            tasks = build['tasks']
            task_count = len(tasks)
            for task in tasks:
                if task['status'] == 'success':
                    success_count = success_count + 1
                elif task['status'] == 'failed':
                    failed_count = failed_count + 1
            line_start = None
            if failed_count > 0:
                build_status = 'failed'
                if sys.stdout.isatty():
                    line_start = bcolors.RED
            elif success_count == task_count:
                build_status = 'success'
                if sys.stdout.isatty():
                    line_start = bcolors.GREEN
            else:
                build_status = 'incomplete'
            line += build_status
            line += ','
            line += str(task_count)
            line += ','
            line += str(success_count)
            line += ','
            line += str(failed_count)
            colorprint(line_start, line)

class bcolors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
def colorprint(color, text):
    if color and sys.stdout.isatty():
        sys.stdout.write(color)
    print(text)
    if color and sys.stdout.isatty():
        sys.stdout.write(bcolors.ENDC)

main()
