#!/bin/bash
count=`ps -ef | grep "add_router_after_reboot.sh" | grep -v grep | awk '{print $2}' | wc -w`
echo count=$count
if [ $count -gt 2 ]
then
    echo "add route progress existed"
    exit 0
fi

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

