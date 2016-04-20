#!/bin/bash
ADD_ROUTER_TEMPLATE=add_router.template
ADD_ROUTER_SH=./patches_tool/aws_patch/add_router.sh

openstack_api_subnet=$1
aws_api_gw=$2
openstack_tunnel_subnet=$3
aws_tunnel_gw=$4

if [ -f ${ADD_ROUTER_SH} ]; then
    echo "delete add_router.sh ..."
    rm ${ADD_ROUTER_SH}
fi

echo "copy add_router.template ..."
cp ${ADD_ROUTER_TEMPLATE} ${ADD_ROUTER_SH}

echo "config add_router.sh ..."
sed -i "s#%openstack_api_subnet%#${openstack_api_subnet}#" ${ADD_ROUTER_SH}
sed -i "s/%aws_api_gw%/${aws_api_gw}/" ${ADD_ROUTER_SH}
sed -i "s#%openstack_tunnel_subnet%#${openstack_tunnel_subnet}#" ${ADD_ROUTER_SH}
sed -i "s/%aws_tunnel_gw%/${aws_tunnel_gw}/" ${ADD_ROUTER_SH}

echo "config add_router.sh success"

