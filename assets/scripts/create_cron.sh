#!/bin/bash
cmd="/usr/local/bin/docker-or-podman exec $1 bash /usr/local/bin/daily_backup 1> /dev/null"
mkdir -p /etc/cron.daily
echo "#!/bin/sh" > /etc/cron.daily/backup_$1
echo "# Run daily backup for $1" >> /etc/cron.daily/backup_$1
if [ "$2" ];then
    echo "MAILTO=$2"
fi
echo $cmd >> /etc/cron.daily/backup_$1
chmod +x /etc/cron.daily/backup_$1
