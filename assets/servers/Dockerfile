FROM python:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://gitlab.dkrz.de/freva/deployment.git"

ENV PORT="5008"
ENV SERVER_FILE="/var/freva/servers.toml"
COPY restservice.py /usr/local/bin/restservice
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools toml &&\
    pip3 install requests flask flask_restful &&\
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf &&\
    mkdir -p /var/freva && chmod +x /usr/local/bin/restservice
EXPOSE $PORT
VOLUME /var/freva/
CMD ["/usr/local/bin/restservice"]
