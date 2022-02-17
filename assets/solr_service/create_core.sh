#!/bin/bash

if [ ! -d /var/solr/data/$1 ];then
    precreate-core $1
    cp managed-schema /var/solr/data/$1/conf/
fi
