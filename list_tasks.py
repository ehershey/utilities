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

user = todoist.login(email = todoist_auth.email, password = todoist_auth.password)

tasks = user.search_tasks("overdue, today, & p:Inbox")

for task in tasks:
  print task.content
