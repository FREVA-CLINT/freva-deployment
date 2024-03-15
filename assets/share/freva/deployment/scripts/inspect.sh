# Simple script that lets us inspect stuff
#
if [ $(whoami) == "root" ];then
    order=(docker podman)
else
    order=(podman)
fi
path=""

for cmd in ${order[*]};do
    if [ "$(which $cmd 2> /dev/null)" ];then
        path=$(which $cmd)
    fi
done

if [ -z "$path" ];then
    echo "Docker nor Podman not on the system."
    exit 1
fi

$path inspect $1 --format='{{index .Config.Labels "org.opencontainers.image.version"}}' 2> /dev/null
