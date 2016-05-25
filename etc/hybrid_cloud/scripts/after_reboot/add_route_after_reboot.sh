#!/bin/bash
let i=0
until ifconfig external_api |grep 'inet addr'
do
    sleep 1s
    echo sleep $i
    ((i++==6000)) && exit
done

add_route_script=/home/hybrid_cloud/scripts/after_reboot/add_vpn_route/*.sh
if [ -e ${add_route_script} ]
then
    sh ${add_route_script}
fi
