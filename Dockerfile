from docker.io/alpine
ARG VERSION
LABEL org.opencontainers.image.authors="DRKZ-CLINT"
LABEL org.opencontainers.image.source="https://github.com/FREVA-CLINT/freva-deployment.git"
LABEL org.opencontainers.image.version="$VERSION"
RUN set -ex &&\
    apk add --no-cache python3 py3-pip py3-cryptography openssh-client sshpass \
    binutils zlib-dev musl-dev libc-dev  libffi-dev gcc g++ pwgen git \
    ansible ansible-core py3-appdirs py3-rich py3-mysqlclient \
    py3-yaml py3-toml py3-tomlkit py3-requests py3-appdirs && \
    apk add --no-cache --virtual /root/build-deps build-base python3-dev \
    libffi-dev openssl-dev rust cargo  &&\
    mkdir -p /opt/freva-deployment &&\
    ln -sf python3 /usr/bin/python && \
    mkdir -p /tmp/deployment
# Install pycrypto so --key can be used with PyInstaller
RUN python3 -m pip install --break-system-packages pycrypto
# Build bootloader for alpine
RUN git clone https://github.com/pyinstaller/pyinstaller.git /tmp/pyinstaller \
    && cd /tmp/pyinstaller/bootloader \
    && CFLAGS="-Wno-stringop-overflow -Wno-stringop-truncation" python ./waf configure all \
    && python3 -m pip install --break-system-packages .. \
    && rm -Rf /tmp/pyinstaller

WORKDIR /tmp/deployment
COPY . .
RUN set -ex &&\
    python3 src/freva_deployment/__init__.py &&\
    python3 -m pip install --break-system-packages . &&\
    rm -rf /root/.cache/pip &&\
    rm -rf /var/cache/apk/* &&\
    apk del /root/build-deps &&\
    rm -rf /root/build-deps &&\
    rm -rf /tmp/deployment
WORKDIR /opt/freva-deployment
VOLUME /opt/freva-deployment
CMD ["/usr/bin/deploy-freva"]
