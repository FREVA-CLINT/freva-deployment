#!/bin/bash
content='[Install]\n
WantedBy=multi-user.target\n\n[Service]\n
Type=simple\n
RemainAfterExit=true\n
ExecStart=sh -c "echo starting docker services"\n[Unit]\n
Description=Start/Stop freva services docker containers\n
After=network-online.target
'
suffix=$(echo $1|rev|cut -d - -f1|rev)
project_name=$(echo $1|sed "s/-${suffix}//g")
#if [ ! -f "/etc/systemd/system/${project_name}.service" ];then
#    echo -e $content > /etc/systemd/system/${project_name}.service
#fi
#if [ -z "$(cat etc/systemd/system/${project_name}.service |grep ${1})" ];then
#    echo " Requires=${1}.service" >> /etc/systemd/system/${project_name}.service
#fi
systemctl daemon-reload
systemctl enable $1 #$project_name
systemctl restart $1 #$project_name
