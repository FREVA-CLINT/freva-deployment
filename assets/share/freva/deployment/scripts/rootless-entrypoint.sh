#!/bin/bash
set -Eeuo pipefail
_setup_mariadb() {
    if [ ! -f "/etc/mysql/conf.d/root.cnf" ];then
        mkdir -p /var/lib/mysql/backup
        echo "[mysqld]" > /etc/mysql/conf.d/root.cnf
        echo "   user=root" >> /etc/mysql/conf.d/root.cnf
    fi
}

_setup_mongodb(){
    DIR_OWNER=$(stat -c '%U' "/data/configdb")
    if [ "$DIR_OWNER" != "root" ]; then
        chown -R root:0 /data/configdb
    fi
    echo "starting mongo without authentication"
    mongod --bind_ip_all --fork
    echo "creating user ..."
    mongosh --eval 'use admin; db.createUser({user: "mongo", pwd: "{{root_passwd}}", roles: [{ role: "root", db: "admin" }]});'
    export MONGO_INITDB_ROOT_USERNAME=mongo
    export MONGO_INITDB_ROOT_PASSWORD={{root_passwd}}
    echo "restarting mongo with authentication enabled..."
    mongod --shutdown
    COMMAND="mongod --bind_ip_all --auth"
}

COMMAND=${@:-redis-server}
if [ "$(which mongod)" ];then
    _setup_mongodb
    COMMAND=${@:-mongod}
elif [ "$(which mariadbd)" ];then
    _setup_mariadb
    COMMAND=${@:-mariadbd}
fi


# Path to the original entrypoint script
ORIGINAL_ENTRYPOINT=$(which docker-entrypoint.sh)
if [ -z "$ORIGINAL_ENTRYPOINT" ];then
    exec "$COMMAND"
fi
TEMP_ENTRYPOINT="/tmp/docker-entrypoint.sh"
cp $ORIGINAL_ENTRYPOINT $TEMP_ENTRYPOINT
sed -i 's/"0"/"-1"/g' "$TEMP_ENTRYPOINT"
sed -i "``s/'0'/'-1'/g" "$TEMP_ENTRYPOINT"
exec $TEMP_ENTRYPOINT "$COMMAND"
