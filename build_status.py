#!/usr/bin/python

import requests

URL = 'https://evergreen.mongodb.com/json/timeline/mongodb-mongo-master?limit=1&skip=0'

response = requests.get(URL)
data = response.json()

print "Build Variant,Status, Total, Success Count, Failed count"
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
                success_count =                 success_count + 1
            elif task['status'] == 'failed':
                failed_count =                 failed_count + 1
        if failed_count > 0:
            build_status = 'failed'
        elif success_count == task_count:
            build_status = 'success'
        else:
            build_status = 'incomplete'
        line += build_status
        line += ','
        line += str(task_count)
        line += ','
        line += str(success_count)
        line += ','
        line += str(failed_count)
        print line
