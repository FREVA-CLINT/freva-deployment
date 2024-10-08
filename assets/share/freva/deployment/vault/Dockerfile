FROM docker.io/hashicorp/vault:latest
ARG VERSION
LABEL org.opencontainers.image.authors="DRKZ-CLINT"
LABEL org.opencontainers.image.source="https://github.com/FREVA-CLINT/freva-deployment.git"
LABEL org.opencontainers.image.version="$VERSION"

ENV VAULT_ADDR='http://127.0.0.1:8200'
ENV VERSION=$VERSION
ENV HOME=/vault
COPY runserver.py /bin/runserver.py
COPY add-vault-secret /bin/add-vault-secret
RUN apk add --update --no-cache gcc musl-dev python3-dev py3-pip libffi-dev build-base
RUN set -ex &&\
    mkdir -p /opt/vault && chown -R vault:vault /opt/vault &&\
    chmod +x /bin/runserver.py /bin/add-vault-secret &&\
    mkdir -p /data && chown -R vault:vault /data &&\
    ln -sf python3 /usr/bin/python
COPY --chown=vault:vault vault-server-tls.hcl /opt/vault/
COPY --chown=vault:vault policy-file.hcl /opt/vault/

RUN python3 -m pip install --break-system-packages --no-cache-dir --upgrade pip setuptools &&\
    python3 -m pip install --break-system-packages --no-cache-dir hvac requests pyopenssl fastapi uvicorn &&\
    rm -rf /root/.cache/pip /var/cache/apk/* /tmp/*

EXPOSE 5002
VOLUME /vault
CMD python3 /bin/runserver.py &&\
    uvicorn --workers 2 --app-dir /bin runserver:app \
    --host 0.0.0.0 --port 5002
