FROM alpine:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://gitlab.dkrz.de/freva/deployment.git"

ARG project="freva-ces"
ARG rootpw=""
ARG db_user=""

ENV ROOT_PW=${rootpw}
ENV DB_USER=${db_user}
ENV PROJECT=${project}
COPY rotate_passwd /usr/local/bin/
COPY backup_rotate /usr/local/bin/
COPY startup /usr/local/bin/
RUN set -ex && \
    chmod +x /usr/local/bin/rotate_passwd &&\
    chmod +x /usr/local/bin/backup_rotate &&\
    chmod +x /usr/local/bin/startup &&\
    apk add --update --no-cache python3 mysql mysql-client rsync &&\
    ln -sf python3 /usr/bin/python


RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools &&\
    pip3 install requests &&\
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf

VOLUME /etc/periodic
CMD ["/usr/local/bin/startup"]
