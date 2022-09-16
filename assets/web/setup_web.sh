#!/bin/bash
export PATH=/opt/condaenv/bin:$PATH
export DJANGO_SUPERUSER_PASSWORD=$1
export DJANGO_SUPERUSER_EMAIL=admin@freva.de
if [ -z $1 ];then
    echo "Usage: $0 django_passwd"
    exit 1
fi

python manage.py migrate --fake contenttypes
python manage.py migrate --fake-initial --noinput
python manage.py collectstatic --noinput
python manage.py createsuperuser \
    --noinput \
    --username freva-admin \
    --email $DJANGO_SUPERUSER_EMAIL || echo 0
# python manage.py shell -c 'Site.objects.all().delete()'
python manage.py shell -c \
    'from django.contrib.sites.models import Site; Site.objects.create(id=1, domain="example.com", name="example.com").save()' || echo 0
