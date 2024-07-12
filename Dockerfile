from docker.io/alpine
ARG VERSION
LABEL org.opencontainers.image.authors="DRKZ-CLINT"
LABEL org.opencontainers.image.source="https://github.com/FREVA-CLINT/freva-deployment.git"
LABEL org.opencontainers.image.version="$VERSION"
RUN set -ex &&\
    apk add --no-cache python3 py3-pip openssh-client sshpass &&\
    apk add --no-cache --virtual /root/build-deps build-base python3-dev \
    libffi-dev openssl-dev rust cargo &&\
    mkdir -p /opt/freva-deployment &&\
    ln -sf python3 /usr/bin/python && \
    mkdir -p /tmp/deployment
WORKDIR /tmp/deployment
COPY . .
RUN set -ex &&\
    python3 src/freva_deployment/__init__.py &&\
    python3 -m pip install --break-system-packages . &&\
    python3 -m pip install --break-system-packages pyinstaller &&\
    rm -rf /root/.cache/pip &&\
    rm -rf /var/cache/apk/* &&\
    apk del /root/build-deps &&\
    rm -rf /root/build-deps &&\
    rm -rf /tmp/deployment
WORKDIR /opt/freva-deployment
VOLUME /opt/freva-deployment
CMD ["/usr/bin/deploy-freva"]
