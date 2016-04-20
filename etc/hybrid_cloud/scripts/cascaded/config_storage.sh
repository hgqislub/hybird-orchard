#!/usr/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/config_storage_run.sh
LOG=${dir}/config_storage_run.log

az_domain=${1}

ifs=$IFS
IFS='.' arr=(${az_domain})
IFS=${ifs}

az_localaz=${arr[0]}
az_localdz=${arr[1]}
az_region=${az_localaz}"."${az_localdz}

backup_az_domain=${2}

ifs=$IFS
IFS='.' arr=(${backup_az_domain})
IFS=${ifs}

backup_az_localaz=${arr[0]}
backup_az_localdz=${arr[1]}
backup_az_region=${az_localaz}"."${az_localdz}

. /root/env.sh

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}
echo ". /root/env.sh" >> ${RUN_SCRIPT}

echo cps host-template-instance-operate --action stop --service cinder cinder-volume >> ${RUN_SCRIPT}
echo sleep 1s >> ${RUN_SCRIPT}
echo cps host-template-instance-operate --action start --service cinder cinder-volume >> ${RUN_SCRIPT}
echo sleep 1s >> ${RUN_SCRIPT}

echo cinder type-create magnetic@${az_region} >> ${RUN_SCRIPT}
echo cinder type-key magnetic@${az_region} set volume_backend_name=AMAZONEC2 >> ${RUN_SCRIPT}

echo cinder type-create hybrid@${az_region}  >> ${RUN_SCRIPT}
echo cinder type-key hybrid@${az_region} set volume_backend_name=HYBRID:${az_region}:${backup_az_region} >> ${RUN_SCRIPT}

echo cps host-template-instance-operate --action stop --service cinder cinder-volume >> ${RUN_SCRIPT}
echo sleep 1s >> ${RUN_SCRIPT}
echo cps host-template-instance-operate --action start --service cinder cinder-volume >> ${RUN_SCRIPT}
echo sleep 1s >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1
