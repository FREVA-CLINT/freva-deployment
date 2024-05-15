from docker.io/alpine
ARG VERSION
LABEL org.opencontainers.image.authors="DRKZ-CLINT"
LABEL org.opencontainers.image.source="https://github.com/FREVA-CLINT/freva-deployment.git"
LABEL org.opencontainers.image.version="$VERSION"
RUN set -ex &&\
    apk add --no-cache python3 py3-pip openssh-client sshpass &&\
    mkdir -p /opt/freva-deployment &&\
    ln -sf python3 /usr/bin/python && \
    mkdir -p /tmp/deployment
WORKDIR /tmp/deployment
COPY . .
RUN set -ex &&\
    python3 src/freva_deployment/__init__.py &&\
    python3 -m pip install --break-system-packages . &&\
    rm -rf /root/.cache/pip &&\
    rm -rf /var/cache/apk/* &&\
    rm -rf /tmp/deployment
WORKDIR /opt/freva-deployment
VOLUME /opt/freva-deployment
CMD ["/usr/bin/deploy-freva"]
