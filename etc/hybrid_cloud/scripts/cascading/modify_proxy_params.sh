#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/modify_proxy_params

RUN_SCRIPT=${dir}/modify_proxy_params_run.sh
RUN_LOG=${dir}/modify_proxy_params_run.log

rm -rf ${dir}
mkdir -p ${dir}

proxy_num=${1}
ext_net_name=${2}

. /root/adminrc
ext_net_id=`neutron net-list | grep ${ext_net_name} | awk -F '|' '{print $2}' | awk '{print $1}'`

if [ -z "${ext_net_id}" ]; then
    sleep 0.5s
    ext_net_id=`neutron net-list | grep ${ext_net_name} | awk -F '|' '{print $2}' | awk '{print $1}'`
fi

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo cps template-params-update --parameter agent_mode=dvr_snat --service neutron neutron-l3-${proxy_num} >> ${RUN_SCRIPT}
echo cps template-params-update --parameter gateway_external_network_id=${ext_net_id} --service neutron neutron-l3-${proxy_num} >> ${RUN_SCRIPT}
echo cps template-params-update --parameter resource_tracker_synced=True --service nova nova-${proxy_num} >> ${RUN_SCRIPT}
echo cps commit >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

