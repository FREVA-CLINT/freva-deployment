#!/bin/bash
cmd="/usr/local/bin/docker-or-podman exec $1 bash /usr/local/bin/daily_backup 1> /dev/null"
# Function to check if the cron job already exists in the crontab
cron_job_exists() {
    local cmd="$1"
    crontab -l 2>/dev/null | grep -F "$cmd" >/dev/null
}
if [ -w /etc/cron.daily ]; then
    # If /etc/cron.daily is writable, create the cron job there
    cron_dir="/etc/cron.daily"
    cron_file="$cron_dir/backup_$1"
else
    # If /etc/cron.daily is not writable, add the cron job to the user's crontab
    cron_dir=""
    cron_file="user"
fi


if [ "$cron_dir" ]; then
    mkdir -p "$cron_dir"
    echo "#!/bin/sh" > "$cron_file"
    echo "# Run daily backup for $1" >> "$cron_file"
    if [ "$2" ]; then
        echo "MAILTO=$2" >> "$cron_file"
    fi
    echo "$cmd" >> "$cron_file"
    chmod +x "$cron_file"
else
     if ! cron_job_exists "$cmd"; then
        echo "0 0 * * * $cmd" >> "$HOME/.crontab"
        crontab "$HOME/.crontab"
    fi
fi
