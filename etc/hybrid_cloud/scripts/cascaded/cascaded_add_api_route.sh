#!/usr/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/cascaded_add_api_route_run.sh
LOG=${dir}/cascaded_add_api_route_run.log

subnet=${1}
gw=${2}

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}

echo "ip route show | grep ${subnet} && ip route del ${subnet}" >> ${RUN_SCRIPT}
echo "ip route add ${subnet} via ${gw}" >> ${RUN_SCRIPT}

echo "ip route show table external_api | grep ${subnet} && ip route del table external_api ${subnet}" >> ${RUN_SCRIPT}
echo "ip route add table external_api ${subnet} via ${gw}" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1
