#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remove_aggregate_run.sh
RUN_LOG=${dir}/remove_aggregate_run.log

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
id_list=`nova aggregate-list | grep ${az_region} | awk -F"|" '{print $2}'`
for id in `echo ${id_list}`
do
    echo sleep 1s >> ${RUN_SCRIPT}
    echo nova aggregate-remove-host ${id} ${az_region} >> ${RUN_SCRIPT}
    echo nova aggregate-delete ${id} >> ${RUN_SCRIPT}
done

nova_service_id=`nova service-list | grep ${az_region} | awk -F "|" '{print $2}'`
echo nova service-disable ${az_region} nova-compute >> ${RUN_SCRIPT}
echo nova service-delete ${nova_service_id} >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1
