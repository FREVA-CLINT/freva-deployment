FROM archlinux:latest
ARG PROJECT_NAME=''
ENV PROJECT_NAME=${PROJECT_NAME}
ENV PYTHONUNBUFFERED 1
ARG git_url=''
ARG git_branch=''
ARG root_dir=''
ARG git_url=''
ARG git_branch=''
ARG build_root=''
ARG core_branch=''
ARG core_url=''
ARG UID=33
ARG GID=33
ENV GIT_BRANCH=${git_branch}
ENV GIT_URL=${git_url}
ENV PROJECT_ROOT=/srv/http
ENV ROOT_DIR=${root_dir}
COPY ./docker_cmd.sh /usr/local/bin/
COPY ./setup_web.sh /tmp
COPY ./freva_web.conf /etc
COPY ./add-aur.sh /root
RUN pacman -Syu --noconfirm --noprogressbar && \
    pacman -S --noconfirm --noprogressbar \
    git vim curl nodejs-nopt apache uwsgi-plugin-python python-pip \
    python-xarray python-pymysql python-ldap python-memcached \
    python-requests python-scipy python-sphinx python-toml \
    python-paramiko python-pylint python-pillow flake8 \
    nodejs python-nose python-mysqlclient python-mock \
    ipython imagemagick python-gitpython ffmpeg fabric \
    python-django-rest-framework python-django python-dask \
    python-distributed python-coverage python-bleach \
    python-markdown python-swiftclient python-pytest-html  \
    python-pytest-env python-django-compressor  \
    python-redis python-hiredis \
    python-django-debug-toolbar python-testpath &&\
    git clone -b $core_branch $core_url /tmp/backend && bash /root/add-aur.sh aur
RUN aur-install mod_wsgi a2enmod-git npm && \
    /usr/bin/python -m pip install /tmp/backend && rm -r /tmp/backend &&\
    /usr/bin/python -m pip install \
    mod-wsgi \
    hurry.filesize \
    django-auth-ldap \
    django-bootstrap-v5 \
    django-datatable-view \
    django-debug-toolbar-user-panel \
    django-discover-runner \
    django-model-utils \
    django-templated-email \
    PyPDF2 \
    pygtail \
    django-debug-toolbar \
    django-ipware \
    django-nose \
    django-datatable-view-compat \
    django-webpack-loader

RUN a2enmod ssl && a2enmod headers &&\
    usermod -u $UID http &&\
    groupmod -g $GID http &&\
    echo "IncludeOptional /srv/http/freva_web.conf" >> /etc/httpd/conf/httpd.conf
ENV EVALUATION_SYSTEM_CONFIG_FILE=${root_dir}/freva/evaluation_system.conf
COPY ./entrypoint.sh /usr/local/bin

CMD ["bash", "/usr/local/bin/docker_cmd.sh"]
EXPOSE 80 443 8000 6379
ENTRYPOINT ["bash","/usr/local/bin/entrypoint.sh"]
WORKDIR ${PROJECT_ROOT}
