FROM vault:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://github.com/FREVA-CLINT/freva.git"

ARG project="freva-ces"
ARG rootpw=""
ARG db_user=""
ARG db_passwd=""
ARG db_name=""

ENV VAULT_ADDR='http://127.0.0.1:8200'
ENV ROOT_PW=${rootpw}
COPY runserver.py /bin/runserver
COPY --chown=vault:vault vault-server-tls.hcl /vault
COPY --chown=vault:vault policy-file.hcl /vault
RUN set -ex &&\
    chmod +x /bin/runserver &&\
    mkdir -p /data && chown -R vault:vault /data &&\
    apk add --update --no-cache python3 mysql mysql-client &&\
    ln -sf python3 /usr/bin/python

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools &&\
    pip3 install requests flask flask_restful

EXPOSE 5002
VOLUME /vault/file
CMD ["/bin/runserver"]
