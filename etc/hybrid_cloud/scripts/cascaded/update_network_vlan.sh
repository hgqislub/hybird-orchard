#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/update_network_vlan

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/update_network_vlan_run.sh
RUN_LOG=${dir}/update_network_vlan_run.log

NET_NAME=${1}
VLAN=${2}

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo "cps network-update --name ${NET_NAME} --vlan ${VLAN}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1