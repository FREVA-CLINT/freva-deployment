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
image=$($path image ls --filer reference=$1 2> /dev/null)
if [ "$image" ];then
    tag=$(echo $image|awk '{print $2}'|grep -iv tag|grep -iv none|grep -iv latest|sort | tail -n 1)
    if [ $tag ];then
        version=$($path inspect $1:$tag --format='{{index .Config.Labels "org.opencontainers.image.version"}}')
        if [ "$version" ];then
            echo $version
        else # Fall back
            echo $tag
        fi
    fi
else
    echo "0.0.0"
fi
