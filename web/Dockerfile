FROM ubuntu:latest
ARG PROJECT_NAME=''
ENV PROJECT_NAME=${PROJECT_NAME}
ENV PYTHONUNBUFFERED 1
ARG git_url=''
ARG git_branch=''
ARG root_dir=''
ARG git_url=''
ARG git_branch=''
ARG build_root=''
ARG backend_branch=''
ARG backend_url=''
ARG conda='/var/www/html/app/venv'
ENV GIT_BRANCH=${git_branch}
ENV GIT_URL=${git_url}
ENV PROJECT_ROOT=/var/www/html/app
ENV ROOT_DIR=${root_dir}
ARG python_version='3.9'
WORKDIR /tmp/freva_web
COPY ./docker_cmd.sh /usr/local/bin/
COPY ./freva_web.conf /tmp/
ENV PATH=/var/www/html/app/venv/bin:${PATH}
RUN apt-get update -y
RUN LC_ALL=C DEBIAN_FRONTEND=noninteractive  apt-get install -y git apt-utils\
    vim curl default-libmysqlclient-dev lynx npm libsasl2-dev apache2 apache2-dev apache2-utils\
    nodejs npm git software-properties-common &&\
    mkdir -p /var/log/apache2&& rm -rf /var/www/html/app
RUN mkdir -p /var/www/html/app&&\
    rm -fr /etc/apache2/logs && ln -s /var/log/apache2 /etc/apache2/logs &&\
    git clone -b $git_branch $git_url /var/www/html/app
RUN cd /var/www/html/app && git pull origin $git_branch
RUN git clone -b $backend_branch $backend_url /tmp/backend &&\
rm -fr /etc/apache2/logs && ln -s /var/log/apache2 /etc/apache2/logs &&\
    python3 /var/www/html/app/deploy.py --prefix $conda --python 3.9 &&\
    $conda/bin/python -m pip install -I -r /tmp/freva_web/requirements.txt &&\
    $conda/bin/python -m pip install /tmp/backend && rm -r /tmp/backend &&\
    $conda/bin/python -m pip install mod_wsgi-standalone &&\
    mkdir -p /var/www/html/app/static/preview && a2enmod ssl && a2enmod headers &&\
    mkdir -p ${root_dir}
RUN PATH=$conda/bin:$PATH $conda/bin/mod_wsgi-express install-module > /etc/apache2/sites-available/000-default.conf &&\
    cat /tmp/freva_web.conf >> /etc/apache2/sites-available/000-default.conf
ENV PUBKEY=${root_dir}/share/freva/${PROJECT_NAME}.crt
ENV EVALUATION_SYSTEM_CONFIG_FILE=${root_dir}/etc/evaluation_system.conf
COPY ./entrypoint.sh /usr/local/bin
CMD ["bash", "/usr/local/bin/docker_cmd.sh"]
EXPOSE 80 443 8000
ENTRYPOINT ["bash","/usr/local/bin/entrypoint.sh"]
WORKDIR /var/www/html/app
