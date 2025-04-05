#!/bin/bash
# Simple script that lets us inspect stuff
#
order=(podman docker)
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
image=$($path image ls --filter reference=$1 --format "table {{.Tag}}" | grep -iv tag 2> /dev/null)
if [ "$image" ];then
    tag=$(echo $image|awk '{print $0}')
    if [ "$tag" ];then
        version=$($path inspect $1:$tag --format='{{index .Config.Labels "org.opencontainers.image.version"}}' 2> /dev/null)
        if [ "$version" ];then
            echo $version
            exit 0
        else # Fall back
            echo $tag
            exit 0
        fi
    fi
else
    echo ""
fi
