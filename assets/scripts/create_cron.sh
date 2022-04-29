#!/bin/bash
cmd="docker exec $1 /usr/local/bin/daily_backup"
cron_job="0 4 * * * $cmd"
already=$(crontab -l | grep "${cmd}")
if [ -z "${already}" ];then
    (crontab -l 2>/dev/null; echo "${cron_job}") | crontab -
fi
