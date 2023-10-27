#!/bin/bash
# Replace USER:PASS with appropriate username/password
# Set this with crontab to run every day @ midnight
# 0 0 * * * /path/to/upc-api/backup.sh >/dev/null 2>&1
curl -X POST -H "Authorization: USER:PASS" http://127.0.0.1:9000/api/admin/backup/