#!/usr/bin/python
from pytodoist import todoist
import todoist_auth
import numerousapp

METRIC_ID = 342440214103810868

user = todoist.login(email = todoist_auth.email, password = todoist_auth.password)

tasks = user.search_tasks("overdue, today")

numerousapp.update_metric_value(METRIC_ID, len(tasks))
