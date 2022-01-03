FROM solr:latest

USER root
LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://gitlab.dkrz.de/freva/deployment.git"
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf
VOLUME /var/solr/data
USER solr
