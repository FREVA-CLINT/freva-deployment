FROM docker.io/hashicorp/vault:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://github.com/FREVA-CLINT/freva.git"

ENV VAULT_ADDR='http://127.0.0.1:8200'
COPY runserver.py /bin/runserver.py
COPY --chown=vault:vault vault-server-tls.hcl /vault
COPY --chown=vault:vault policy-file.hcl /vault
RUN set -ex &&\
    chmod +x /bin/runserver.py &&\
    mkdir -p /data && chown -R vault:vault /data &&\
    apk add --update --no-cache python3 mysql mysql-client &&\
    ln -sf python3 /usr/bin/python

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools &&\
    pip3 install requests pyopenssl fastapi uvicorn

EXPOSE 5002
VOLUME /vault/file
CMD /bin/runserver.py &&\
    uvicorn --workers 2 --app-dir /bin runserver:app \
    --host 0.0.0.0 --port 5002
