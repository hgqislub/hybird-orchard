#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/add_vpn_tunnel_route

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/add_vpn_tunnel_route_run.sh
RUN_LOG=${dir}/add_vpn_tunnel_route_run.log

openstack_tunnel_subnet=${1}
aws_tunnel_gw=${2}

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}

echo "ip route show | grep ${openstack_tunnel_subnet} && ip route del ${openstack_tunnel_subnet}" >> ${RUN_SCRIPT}
echo "ip route add ${openstack_tunnel_subnet} via ${aws_tunnel_gw}" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1
