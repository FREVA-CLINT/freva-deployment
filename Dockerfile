FROM debian:bookworm

ARG VERSION
LABEL org.opencontainers.image.authors="DRKZ-CLINT"
LABEL org.opencontainers.image.source="https://github.com/FREVA-CLINT/freva-deployment.git"
LABEL org.opencontainers.image.version="$VERSION"

# Install required packages including locales
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-cryptography \
    python3-dev \
    python3-pip \
    openssh-client \
    sshpass \
    git \
    binutils \
    libghc-zlib-dev \
    musl-dev \
    librust-libc-dev \
    libc-devtools \
    libffi-dev \
    gcc \
    g++ \
    python3-appdirs \
    python3-mysqldb \
    python3-yaml \
    python3-toml \
    python3-tomlkit \
    python3-requests \
    ansible \
    python3-mock \
    mysql-common \
    locales && \
    rm -rf /var/lib/apt/lists/*

# Generate and set the desired locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8

# Set environment variables for locale
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Set up work directories
RUN mkdir -p /opt/freva-deployment /tmp/deployment /src

WORKDIR /tmp/deployment

# Copy all files into the container
COPY . .

# Install Python dependencies
RUN python3 src/freva_deployment/__init__.py && \
    python3 -m pip install --break-system-packages pyinstaller . && \
    python3 pyinstaller/pre-win.py &&\
    rm -rf /root/.cache/pip && \
    rm -rf /root/build-deps && \
    rm -rf /tmp/deployment

WORKDIR /opt/freva-deployment

# Define volumes
VOLUME /opt/freva-deployment
VOLUME /src

# Define the default command
CMD ["/usr/local/bin/deploy-freva"]
