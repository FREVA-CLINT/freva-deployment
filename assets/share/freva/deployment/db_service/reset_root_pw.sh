#!/bin/bash
### Reset the root password
set -e


echo "USE mysql; FLUSH PRIVILEGES; ALTER USER "\
     "'root'@'localhost' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD'; "\
     "ALTER USER 'root'@'%' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD'; "\
     "ALTER USER '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD'; "\
     "FLUSH PRIVILEGES;"\
     "GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;"\
     "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;"\
     "FLUSH PRIVILEGES;" > /tmp/my.sql
mariadb -u root < /tmp/my.sql
rm /tmp/my.sql
