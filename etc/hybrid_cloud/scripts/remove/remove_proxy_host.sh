#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/remove_proxy

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/remove_proxy_run.sh
RUN_LOG=${dir}/remove_proxy_run.log

proxy_host_id=${1}
proxy=${2}

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo ". /root/adminrc" >> ${RUN_SCRIPT}
echo "cps role-host-delete --host ${proxy_host_id} blockstorage-${proxy}" >> ${RUN_SCRIPT}
echo "cps role-host-delete --host ${proxy_host_id} compute-${proxy}" >> ${RUN_SCRIPT}
echo "cps role-host-delete --host ${proxy_host_id} network-${proxy}" >> ${RUN_SCRIPT}
echo "cps role-host-delete --host ${proxy_host_id} dhcp" >> ${RUN_SCRIPT}

echo cps commit >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

