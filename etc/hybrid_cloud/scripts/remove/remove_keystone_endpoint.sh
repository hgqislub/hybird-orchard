#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remove_keystone_endpoint_run.sh
RUN_LOG=${dir}/remove_keystone_endpoint_run.log

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
echo "id_list=\`keystone endpoint-list | grep "${az_region}" | awk -F \"|\" '{print \$2}'\`" >> ${RUN_SCRIPT}
echo "for id in \`echo \${id_list}\`" >> ${RUN_SCRIPT}
echo "do" >> ${RUN_SCRIPT}
echo "   keystone endpoint-delete \$id" >> ${RUN_SCRIPT}
echo "done" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

