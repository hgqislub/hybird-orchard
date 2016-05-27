#!/bin/bash
hws_gateway=/home/hybrid_cloud/scripts/patches/patches_tool/hws_patch/hws_gateway/hws_gateway_v0.4.jar

if [ "${1}" == "stop" ]
then
    ps -ef | grep "hws_gateway_v0.4.jar" | grep -v grep | awk '{print $2}' | xargs -l kill -9 >/dev/null 2>&1;
    echo hws_gateway stopped
fi

if [ "${1}" == "start" ] && !(ps -ef | grep "hws_gateway_v" | grep -v grep)
then
    /usr/lib/jre/bin/java -jar $hws_gateway >/dev/null 2>&1 &
    echo hws_gateway started
elif [ "${1}" == "start" ] && (ps -ef | grep "hws_gateway_v" | grep -v grep)
then
    echo hws_gateway already existed
fi

if [ "${1}" == "restart" ]
then
    ps -ef | grep "hws_gateway_v0.4.jar" | grep -v grep | awk '{print $2}' | xargs -l kill -9 >/dev/null 2>&1;
    /usr/lib/jre/bin/java -jar $hws_gateway >/dev/null 2>&1 &
    echo restarted
fi
