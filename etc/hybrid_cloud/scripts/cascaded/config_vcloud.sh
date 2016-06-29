#!/bin/sh
if [ $# != 5 ]; then
    echo "Usage: sh $0 vcloud_host_ip vcloud_org vcloud_vdc vcloud_host_username vcloud_host_password"
    exit 1
fi


NOVA_CONFIG_FILE=/etc/nova/others/cfg_template/nova-compute.json
CINDER_CONFIG_FILE=/etc/cinder/others/cfg_template/cinder-volume.json


vcloud_host_ip=$1
vcloud_org=$2
vcloud_vdc=$3
vcloud_host_username=$4
vcloud_host_password=$5

echo "config nova..."

sed -i "s/%vcloud_host_ip%/${vcloud_host_ip}/" ${NOVA_CONFIG_FILE}
sed -i "s/%vcloud_org%/${vcloud_org}/" ${NOVA_CONFIG_FILE}
sed -i "s/%vcloud_vdc%/${vcloud_vdc}/" ${NOVA_CONFIG_FILE}
sed -i "s/%vcloud_host_username%/${vcloud_host_username}/" ${NOVA_CONFIG_FILE}
sed -i "s/%vcloud_host_password%/${vcloud_host_password}/" ${NOVA_CONFIG_FILE}

echo "config cinder..."

sed -i "s/%vcloud_host_ip%/${vcloud_host_ip}/" ${CINDER_CONFIG_FILE}
sed -i "s/%vcloud_org%/${vcloud_org}/" ${CINDER_CONFIG_FILE}
sed -i "s/%vcloud_vdc%/${vcloud_vdc}/" ${CINDER_CONFIG_FILE}
sed -i "s/%vcloud_host_username%/${vcloud_host_username}/" ${CINDER_CONFIG_FILE}
sed -i "s/%vcloud_host_password%/${vcloud_host_password}/" ${CINDER_CONFIG_FILE}

echo "config success"
exit 0

