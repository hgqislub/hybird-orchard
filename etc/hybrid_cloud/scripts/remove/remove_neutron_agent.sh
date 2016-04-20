#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remote_neutron_agent_run.sh
RUN_LOG=${dir}/remote_neutron_agent_run.log

az_domain=${1}

ifs=$IFS
IFS='.' arr=(${az_domain})
IFS=${ifs}

az_localaz=${arr[0]}
az_localdz=${arr[1]}
az_region=${az_localaz}"."${az_localdz}

. /root/adminrc

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo ". /root/adminrc" >> ${RUN_SCRIPT}

agent_id_list=`neutron agent-list | grep ${az_region} | awk -F "|" '{print $2}'`

for agent_id in `echo ${agent_id_list}`
do
    echo neutron agent-delete ${agent_id} >> ${RUN_SCRIPT}
done

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1
