#!/usr/bin/python
#
#
# List Todoist tasks due today or overdue, excluding "@home" label
#
# See also:
# http://www.todoist.com/
#

from pytodoist import todoist
import todoist_auth
import argparse
DEFAULT_FILTER = "overdue, today, & p:Inbox"

parser = argparse.ArgumentParser(description='List Todoist Tasks')
parser.add_argument('-f', '--filter', help='Filter to search with',
                    default=DEFAULT_FILTER)
parser.add_argument('-e', '--exclude_projects',
                    help='Comma separated list of projects whose tasks \
                          to exclude from output')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Include some extra details')
args = parser.parse_args()

exclude_projects = args.exclude_projects.lower().split(",")

user = todoist.login(email=todoist_auth.email, password=todoist_auth.password)

if args.verbose:
    print "Filter: {0}".format(args.filter)
tasks = user.search_tasks(args.filter)

for task in tasks:
    if task.project and task.project.name and \
       task.project.name.lower() in exclude_projects:
        continue
    if args.verbose:
        print "project: {0}".format(task.project.name)
    print task.content.encode('ascii', 'ignore')
