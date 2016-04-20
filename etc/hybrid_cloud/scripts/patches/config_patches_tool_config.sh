#!/bin/sh
if [ $# != 8 ]; then
    echo "Usage: sh $0 proxy_name proxy_host_name az_domain remote_api_subnet remote_api_gw remote_data_subnet remote_data_gw cascading_domain"
    exit 1
fi
CONFIG_TEMPLATE=patches_tool_config.template
CONFIG_FILE=./patches_tool/patches_tool_config.ini

proxy_name=$1
proxy_host_name=$2
az_domain=$3
openstack_api_subnet=$4
aws_api_gw=$5
openstack_data_subnet=$6
aws_data_gw=$7
cascading_domain=${8}

proxy_match_host=${proxy_name}":"${proxy_host_name}
proxy_match_region=${proxy_name}":"${az_domain}
cascaded_add_route=${openstack_api_subnet}":"${aws_api_gw}","${openstack_data_subnet}":"${aws_data_gw}
cascaded_add_table_external_api=${openstack_api_subnet}":"${aws_api_gw}

if [ -f ${CONFIG_FILE} ]; then
    echo "delete config file ..."
    rm ${CONFIG_FILE}
fi

echo "copy config template ..."
cp ${CONFIG_TEMPLATE} ${CONFIG_FILE}

sed -i "s/%proxy_match_host%/${proxy_match_host}/" ${CONFIG_FILE}
sed -i "s/%proxy_match_region%/${proxy_match_region}/" ${CONFIG_FILE}
sed -i "s#%cascaded_add_route%#${cascaded_add_route}#" ${CONFIG_FILE}
sed -i "s#%cascaded_add_table_external_api%#${cascaded_add_table_external_api}#" ${CONFIG_FILE}
sed -i "s/%cascading_domain%/${cascading_domain}/" ${CONFIG_FILE}

echo "config success"
exit 0
