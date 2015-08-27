#!/usr/bin/python
"""

Mark a Todoist task complete

See also:
http://www.todoist.com/

"""

from pytodoist import todoist
import todoist_auth
import argparse


def complete_task(task):
    print "Marking task complete: " + task.content
    task.complete()

DEFAULT_FILTER = "overdue, today, & p:Inbox"

parser = argparse.ArgumentParser(description='Mark Todoist Task complete')
parser.add_argument('text_to_match', help='Task text')
parser.add_argument('--exact_match_only', action='store_true', help='If task text must be exact (default is substring match)')
parser.add_argument('-v', '--verbose', action='store_true', help='Include some extra details')
args = parser.parse_args()


user = todoist.login(email=todoist_auth.email, password=todoist_auth.password)

tasks = user.search_tasks(DEFAULT_FILTER)

matching_tasks = []
exact_matching_tasks = []

text_to_match = args.text_to_match.lower()

for task in tasks:
    task_content = task.content.lower()
    if text_to_match in task_content:
        matching_tasks.append(task)
    if text_to_match == task_content:
        exact_matching_tasks.append(task)

if len(matching_tasks) == 1 and not args.exact_match_only:
    complete_task(matching_tasks[0])
else:
    if len(exact_matching_tasks) == 1:
        complete_task(exact_matching_tasks[0])
    else:
        print "Invalid length of list of matching tasks: " + str(len(matching_tasks))
