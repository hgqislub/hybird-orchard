#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remove_cinder_service_run.sh
RUN_LOG=${dir}/remove_cinder_service_run.log

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

service_list=`cinder service-list | grep ${az_region} | awk -F"|" '{print $2}'`

for service in `echo ${service_list}`
do
    echo cinder service-disable ${az_region} ${service} >> ${RUN_SCRIPT}
done

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1
