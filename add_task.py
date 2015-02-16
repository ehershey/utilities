#!/usr/bin/python
#
#
# Add Todoist task - due today
#
# See also:
# http://www.todoist.com/
#

import argparse
from pytodoist import todoist
import todoist_auth
import datetime

parser = argparse.ArgumentParser(description='Test packages')
parser.add_argument('--title', help='Task Title', default = None, required = True);
parser.add_argument('--due', help='Due Date', default = "today");
args = parser.parse_args()

user = todoist.login(email = todoist_auth.email, password = todoist_auth.password)

inbox = user.get_project('Inbox')

content = "Test Content"

inbox.add_task(args.title, date = args.due)
