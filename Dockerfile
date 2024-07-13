FROM debian:buster
ARG VERSION
LABEL org.opencontainers.image.authors="DRKZ-CLINT"
LABEL org.opencontainers.image.source="https://github.com/FREVA-CLINT/freva-deployment.git"
LABEL org.opencontainers.image.version="$VERSION"
RUN apt-get update && apt-get install -y build-essential python3-cryptography \
    python3-dev python3-pip openssh-client sshpass
RUN apt-get install -y binutils libghc-zlib-dev musl-dev \
    librust-libc-dev libc-devtools libffi-dev gcc g++
RUN apt-get install -y python3-appdirs python3-mysqldb python3-yaml \
    python3-toml python3-tomlkit python3-requests ansible && \
    mkdir -p /opt/freva-deployment &&\
    mkdir -p /tmp/deployment && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /src
WORKDIR /tmp/deployment
COPY . .
# Install Python dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install pyinstaller ansible &&\
    python3 src/freva_deployment/__init__.py && \
    python3 -m pip install --break-system-packages . && \
    rm -rf /root/.cache/pip && \
    rm -rf /root/build-deps && \
    rm -rf /tmp/deployment
WORKDIR /opt/freva-deployment
VOLUME /opt/freva-deployment
VOLUME /src
CMD ["/usr/bin/deploy-freva"]
