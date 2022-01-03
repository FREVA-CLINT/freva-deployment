FROM vault:latest

LABEL maintainer="DRKZ-CLINT"
LABEL repository="https://gitlab.dkrz.de/freva/deployment.git"

ARG project="freva-ces"
ARG rootpw=""
ARG db_user=""
ARG db_passwd=""
ARG db_name=""

ENV VAULT_ADDR='http://127.0.0.1:8200'
ENV ROOT_PW=${rootpw}
COPY runserver.py /bin/runserver
COPY vault-server-tls.hcl /vault
COPY policy-file.hcl /vault
COPY ${project}.key /mnt/freva.key
COPY ${project}.crt /mnt/freva.crt
RUN set -ex ;\
    chown vault:vault /vault/*.hcl;\
    chown vault:vault /mnt/freva.*;\
    chmod +x /bin/runserver &&\
    mkdir -p /data && chown -R vault:vault /data &&\
    apk add --update --no-cache python3 mysql mysql-client &&\
    ln -sf python3 /usr/bin/python

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools &&\
    pip3 install requests flask flask_restful &&\
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf

EXPOSE 5002
VOLUME /vault/file
CMD ["/bin/runserver"]
