FROM mariadb:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://gitlab.dkrz.de/freva/deployment.git"
ENV NUM_BACKUPS=7
ENV BACKUP_DIR=/var/lib/mysql/backup
RUN apt -y update && apt -y install python3 pip
COPY daily_backup.sh /usr/local/bin/daily_backup
COPY password_rotate.py /usr/local/bin/pwassword_rotate
RUN chmod +x /usr/local/bin/daily_backup /usr/local/bin/pwassword_rotate &&\
    python3 -m pip install requests
