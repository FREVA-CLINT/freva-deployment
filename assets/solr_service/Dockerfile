FROM solr:8.11

USER root
LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://gitlab.dkrz.de/freva/deployment.git"
ENV NUM_BACKUPS=7
ENV CORE="files"
COPY daily_backup.sh /usr/local/bin/daily_backup

RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf &&\
    chmod +x /usr/local/bin/daily_backup
VOLUME /var/solr/data
USER solr
COPY create_core.sh managed-schema ./
