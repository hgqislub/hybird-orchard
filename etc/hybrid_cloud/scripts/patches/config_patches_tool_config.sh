#!/bin/sh
if [ $# != 4 ]; then
    echo "Usage: sh $0 proxy_name proxy_host_name az_domain cascading_domain"
    exit 1
fi
CONFIG_TEMPLATE=patches_tool_config.template
CONFIG_FILE=./patches_tool/patches_tool_config.ini

proxy_name=$1
proxy_host_name=$2
az_domain=$3
cascading_domain=${4}

proxy_match_host=${proxy_name}":"${proxy_host_name}
proxy_match_region=${proxy_name}":"${az_domain}

if [ -f ${CONFIG_FILE} ]; then
    echo "delete config file ..."
    rm ${CONFIG_FILE}
fi

echo "copy config template ..."
cp ${CONFIG_TEMPLATE} ${CONFIG_FILE}

sed -i "s/%proxy_match_host%/${proxy_match_host}/" ${CONFIG_FILE}
sed -i "s/%proxy_match_region%/${proxy_match_region}/" ${CONFIG_FILE}
sed -i "s/%cascading_domain%/${cascading_domain}/" ${CONFIG_FILE}

echo "config success"
exit 0
