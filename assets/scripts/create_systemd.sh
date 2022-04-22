#!/bin/bash

daemon_content=/etc/systemd/system/$1.service
podman=$(which podman)
docker=$(which docker)
docker_fragment=$(systemctl show docker 2> /dev/null|grep -i FragmentPath=)
podman_fragment=$(systemctl show podman 2> /dev/null|grep -i FragmentPath=)
if [ "$docker_fragment" ];then
	sed -i "s#/usr/bin/docker#$docker#g" $daemon_content
else
	sed -i "s#/usr/bin/docker#$podman#g" $daemon_content
 	sed -i "s/docker.service/podman.service/g" $daemon_content
fi
systemctl daemon-reload
systemctl enable $1
systemctl restart $1
