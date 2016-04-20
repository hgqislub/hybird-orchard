#!/bin/sh
#2015.8.18 test ok

LOCAL_CONFIG=/etc/ipsec.d/ipsec.local.conf

tunnel_name=$1
flag="#add for ${tunnel_name}#"
sed -i "/${flag}/,/${flag}/d" ${LOCAL_CONFIG}
