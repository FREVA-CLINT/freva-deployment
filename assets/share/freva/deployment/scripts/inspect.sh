#!/bin/bash
# Simple script that lets us inspect stuff
#
if [ $(whoami) == "root" ];then
    order=(docker podman)
else
    order=(podman)
fi
path=""

for cmd in ${order[*]};do
    if [ "$(which $cmd /dev/null)" ];then
        path=$(which $cmd)
    fi
done

if [ -z "$path" ];then
    echo "Docker nor Podman not on the system."
    exit 1
fi
if [ "$($path images | grep $1)" ];then
    $path inspect $1 --format='{{index .Config.Labels "org.opencontainers.image.version"}}'
fi
