#!/bin/bash
export DJANGO_SUPERUSER_PASSWORD=$1
export DJANGO_SUPERUSER_EMAIL=admin@freva.de
export DJANGO_SUPERUSER_USERNAME=$2
if [ -z $2 ];then
    echo "Usage: $0 django_passwd django_admin_username"
    exit 1
fi

web_dir=$(mktemp -u)
git clone -b $GIT_BRANCH $GIT_URL  $web_dir
cd $PROJECT_ROOT
rm -r ${web_dir}/.git*
cp -r ${web_dir}/* .
rm -r ${web_dir}
mkdir -p ${PROJECT_ROOT}/static/preview
python manage.py migrate --fake contenttypes
python manage.py migrate --fake-initial --noinput
python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
python manage.py collectstatic --noinput
npm install
npm run build-production
python manage.py collectstatic --noinput
