#!/usr/bin/python
#
#
# Post my total number of tasks from Todoist to Numerous, including overdue
# tasks and anything due today.
#
# See also:
# http://www.todoist.com/
# http://www.numerousapp.com/
#

from pytodoist import todoist
import todoist_auth
import numerousapp

METRIC_ID = 342440214103810868

user = todoist.login(email = todoist_auth.email, password = todoist_auth.password)

tasks = user.search_tasks("overdue, today")

numerousapp.update_metric_value(METRIC_ID, len(tasks))
