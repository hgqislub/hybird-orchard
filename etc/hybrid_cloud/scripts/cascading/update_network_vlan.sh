#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/add_network_vlan

RUN_SCRIPT=${dir}/add_network_vlan_run.sh
RUN_LOG=${dir}/add_network_vlan_run.log

rm -rf ${dir}
mkdir -p ${dir}

NETWORK_NAME=${1}
VLAN_ID=${2}

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo ". /root/adminrc" >> ${RUN_SCRIPT}
echo "cps network-update --name ${NETWORK_NAME} --vlan ${VLAN_ID}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1