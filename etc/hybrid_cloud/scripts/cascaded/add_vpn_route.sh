#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/add_vpn_route

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/add_vpn_route_run.sh
RUN_LOG=${dir}/add_vpn_route_run.log

if [ $# == 2 ]; then
    openstack_tunnel_subnet=${1}
    tunnel_gw=${2}
    echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
    echo "ip route show | grep ${openstack_tunnel_subnet} && ip route del ${openstack_tunnel_subnet}" >> ${RUN_SCRIPT}
    echo "ip route add ${openstack_tunnel_subnet} via ${tunnel_gw}" >> ${RUN_SCRIPT}
elif [ $# == 4 ]; then
    openstack_api_subnet=${1}
    api_gw=${2}
    openstack_tunnel_subnet=${3}
    tunnel_gw=${4}
    echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
    echo "ip route show | grep ${openstack_api_subnet} && ip route del ${openstack_api_subnet}" >> ${RUN_SCRIPT}
    echo "ip route show | grep ${openstack_tunnel_subnet} && ip route del ${openstack_tunnel_subnet}" >> ${RUN_SCRIPT}

    echo "ip route add ${openstack_api_subnet} via ${api_gw}" >> ${RUN_SCRIPT}
    echo "ip route add ${openstack_tunnel_subnet} via ${tunnel_gw}" >> ${RUN_SCRIPT}

    echo "ip route show table external_api | grep ${openstack_api_subnet} && ip route del table external_api ${openstack_api_subnet}" >> ${RUN_SCRIPT}
    echo "ip route add table external_api ${openstack_api_subnet} via ${api_gw}" >> ${RUN_SCRIPT}
else
    echo "ip route add failed" >> ${RUN_SCRIPT}
fi

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1