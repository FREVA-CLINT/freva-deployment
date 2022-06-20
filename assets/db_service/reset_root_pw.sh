#!/bin/bash
### Reset the root password
set -e

pw_file=/var/lib/mysql/.pw_file

if [ ! -f "$pw_file" ];then
    echo $MYSQL_ROOT_PASSWORD > $pw_file
fi
root_pw=$(cat $pw_file)
echo "USE mysql; FLUSH PRIVILEGES; ALTER USER "\
     "'root'@'localhost' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD'; "\
     "ALTER USER 'root'@'%' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD'; "\
     "ALTER USER '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD'; "\
     "FLUSH PRIVILEGES;" > /tmp/my.sql
mysql -p$root_pw -u root < /tmp/my.sql
echo $MYSQL_ROOT_PASSWORD > $pw_file
rm /tmp/my.sql
