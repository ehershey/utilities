#!/usr/bin/python
#
# Display Evergreen build status
#
# Usage:
# build_status.py [ --verbose ] [ --push-only ] [ --skip-commits <N> ] [ --include-commits <N> ]
#
# --skip-commits is how many most recent commits to skip
# --include-commits is how many commits to include in success/failed status
# --verbose includes extra information like the URL being requested
# --push-only only displays build variants containing push tasks
#

import argparse
import requests
import sys

URL = 'https://evergreen.mongodb.com/json/timeline/mongodb-mongo-master?limit=%s&skip=%s'


def main():
    parser = argparse.ArgumentParser(description='Build Status')
    parser.add_argument('--verbose','-v', default = False, action='store_true', help='Display info about processing');
    parser.add_argument('--push-only','-p', default = False, action='store_true', help='Only display information from builds with push tasks');
    parser.add_argument('--skip-commits','-s', default = 0, help='How many commits to skip');
    parser.add_argument('--ignore-inactive','-I', default = False, action='store_true', help='Ignore any inactive versions');
    parser.add_argument('--include-commits','-i', default = 1, type=int, help='How many commits to include');
    args = parser.parse_args()

    total_to_skip = args.skip_commits
    total_to_include = args.include_commits

    ignore_inactive = args.ignore_inactive

    # track how many unignored versions we have information for
    #
    unignored_versions_seen = 0

    versions_skipped = 0
    versions_included = 0

    build_variant_map = {}

    colorprint(bcolors.BOLD, "Build Variant,Status, Total, Success Count, Failed count, Incomplete count")

    limit = 10
    skip = 0

    while versions_included < total_to_include:

      url = URL % (limit, skip)

      skip += limit

      if args.verbose:
          print("Requesting %s" % url)

      response = requests.get(url)

      data = response.json()
      for version in data['Versions']:
          if args.verbose:
            print("versions_included: %s" % versions_included)
            print("total_to_include: %s" % total_to_include)
            print("versions_included < total_to_include: %s" % (versions_included < total_to_include))
          is_version_active = False
          builds = version['Builds']

          if versions_included >= total_to_include:
            break

          # Iterate through all builds once to determine if the version is active
          #
          for build in builds:
              build = build['Build']

              if "activated" in build and build['activated'] != False:
                is_version_active = True

          if ignore_inactive and not is_version_active:
            # ignore this versions
            next

          if versions_skipped < total_to_skip:
            versions_skipped += 1
            next

          versions_included += 1


          for build in builds:
              build = build['Build']


              if build['display_name'] in build_variant_map:
                  build_variant_info = build_variant_map[build['display_name']]
              else:
                  build_variant_info = { "success_count": 0, "failed_count": 0, "task_count": 0, "contains_push_task": False}
                  build_variant_map[build['display_name']] = build_variant_info

              tasks = build['tasks']
              tasks = build['tasks']
              build_variant_info['task_count'] += len(tasks)

              for task in tasks:

                  if task['display_name'] == 'push':
                      build_variant_info['contains_push_task'] = True
                  if task['status'] == 'success':
                      build_variant_info['success_count'] = build_variant_info['success_count'] + 1
                  elif task['status'] == 'failed':
                      build_variant_info['failed_count'] = build_variant_info['failed_count'] + 1

    for build_variant in sorted(build_variant_map.keys()):

        build_variant_info = build_variant_map[build_variant]

        if args.push_only and not build_variant_info['contains_push_task']:
            continue

        line=""
        line += build_variant
        line += ","

        line_start = ''


        failed_count = build_variant_info['failed_count']
        success_count = build_variant_info['success_count']
        task_count = build_variant_info['task_count']

        incomplete_count = task_count - failed_count - success_count

        build_status = ''

        if failed_count > 0:
            build_status = 'failed'
            line_start = bcolors.RED
        elif success_count == task_count:
            build_status = 'success'
            line_start = bcolors.GREEN
        else:
            build_status = 'incomplete'

        if build_variant_info['contains_push_task'] and not args.push_only:
            line_start += bcolors.BOLD

        line += build_status
        line += ','
        line += str(task_count)
        line += ','
        line += str(success_count)
        line += ','
        line += str(failed_count)
        line += ','
        line += str(incomplete_count)
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
