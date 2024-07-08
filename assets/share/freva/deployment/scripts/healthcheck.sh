#!/bin/sh
#
exec 3<>/dev/tcp/localhost/"$1"

echo -e "GET $2 HTTP/1.1
host: localhost:$1
" >&3
timeout 1 cat <&3 | grep status | grep UP || exit 1
