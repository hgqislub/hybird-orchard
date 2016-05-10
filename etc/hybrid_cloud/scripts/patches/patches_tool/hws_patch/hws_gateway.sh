#!/bin/bash
ps -ef | grep "hws_gateway_v" | grep -v grep | awk '{print $2}' | xargs -l kill -9;
/usr/lib/jre/bin/java -jar ./hws_gateway/hws_gateway_v0.4.jar >/dev/null 2>&1 &