#!/bin/bash
export DJANGO_SUPERUSER_PASSWORD=$1
export DJANGO_SUPERUSER_EMAIL=admin@freva.de
if [ -z $1 ];then
    echo "Usage: $0 django_passwd"
    exit 1
fi

web_dir=$(mktemp -u)
git clone -b $GIT_BRANCH $GIT_URL  $web_dir
cd $PROJECT_ROOT
rm -fr .git
cp -rT ${web_dir} $PROJECT_ROOT
rm -r ${web_dir}
mkdir -p ${PROJECT_ROOT}/static/preview
cp /etc/freva_web.conf .
python manage.py migrate --fake contenttypes
python manage.py migrate --fake-initial --noinput
python manage.py createsuperuser \
    --noinput \
    --username freva-admin \
    --email $DJANGO_SUPERUSER_EMAIL
python manage.py collectstatic --noinput
npm install
npm run build-production
python manage.py collectstatic --noinput
