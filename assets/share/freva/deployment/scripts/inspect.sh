#!/bin/bash
# Simple script that lets us inspect stuff
#
if [ $(whoami) == "root" ];then
    order=(docker podman)
else
    order=(podman docker)
fi
path=""
for cmd in ${order[*]};do
    if [ "$(which $cmd 2> /dev/null)" ];then
        path=$(which $cmd)
	break
    fi
done
if [ -z "$path" ];then
    echo "Docker nor Podman on the system."
    exit 1
fi
if [ "$($path image ls --filter reference=$1)" ];then
    tag=$($path image ls --filter reference=$1|awk '{print $2}'|grep -iv tag|grep -iv none|grep -iv latest|sort | tail -n 1)
    if [ $tag ];then
        $path inspect $1:$tag --format='{{index .Config.Labels "org.opencontainers.image.version"}}'
    fi
fi
