#!/bin/bash
### Reset the root password
set -e


echo "USE mysql; FLUSH PRIVILEGES; ALTER USER "\
     "'root'@'localhost' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD'; "\
     "ALTER USER 'root'@'%' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD'; "\
     "ALTER USER '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD'; "\
     "FLUSH PRIVILEGES;" > /tmp/my.sql
mysql -u root < /tmp/my.sql
rm /tmp/my.sql
