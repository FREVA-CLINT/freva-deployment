FROM python:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://github.com/FREVA-CLINT/freva.git"

ENV SERVER_FILE="/var/freva/servers.toml"
COPY restservice.py /usr/local/bin/restservice
RUN groupadd -g 9999 python
RUN useradd -ms /bin/bash -d /var/freva python -u 9999 -g 9999
RUN python3 -m ensurepip &&\
    chmod +x /usr/local/bin/restservice &&\
    pip3 install --no-cache --upgrade pip setuptools toml requests flask flask_restful
USER python
VOLUME /var/freva/
CMD ["/usr/local/bin/restservice"]
