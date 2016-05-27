#!/bin/bash
let i=0
until ifconfig external_api |grep 'inet addr'
do
    sleep 1s
    echo sleep $i
    ((i++==6000)) && exit
done

add_route_script=/home/hybrid_cloud/scripts/after_reboot/add_vpn_route
if [ -e ${add_route_script} ]
then
    files=$(find $add_route_script -name "*.sh")
    for file in $files
    do
        sh $file
    done
fi
