#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/add_vpn_route

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/add_vpn_route_run.sh
RUN_LOG=${dir}/add_vpn_route_run.log

api_subnet=${1}
api_gateway=${2}
tunnel_subnet=${3}
tunnel_gateway=${4}

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo "ip route show | grep ${api_subnet} && ip route del ${api_subnet}" >> ${RUN_SCRIPT}
echo "ip route show | grep ${tunnel_subnet} && ip route del ${tunnel_subnet}" >> ${RUN_SCRIPT}

echo "let i=0" >> ${RUN_SCRIPT}
echo "until ip route show | grep ${api_subnet}" >> ${RUN_SCRIPT}
echo "do" >> ${RUN_SCRIPT}
echo "  ip route add ${api_subnet} via ${api_gateway}" >> ${RUN_SCRIPT}
echo "  sleep 1s" >> ${RUN_SCRIPT}
echo "  echo add external api route, sleep \$i" >> ${RUN_SCRIPT}
echo "  ((i++==600)) && exit" >> ${RUN_SCRIPT}
echo "done" >> ${RUN_SCRIPT}

echo "let i=0" >> ${RUN_SCRIPT}
echo "until ip route show | grep ${tunnel_subnet}" >> ${RUN_SCRIPT}
echo "do" >> ${RUN_SCRIPT}
echo "  ip route add ${tunnel_subnet} via ${tunnel_gateway}" >> ${RUN_SCRIPT}
echo "  sleep 1s" >> ${RUN_SCRIPT}
echo "  echo add external api route, sleep \$i" >> ${RUN_SCRIPT}
echo "  ((i++==600)) && exit" >> ${RUN_SCRIPT}
echo "done" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1