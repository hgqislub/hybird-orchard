#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/create_keystone_endpoint

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/create_keystone_endpoint_run.sh
RUN_LOG=${dir}/create_keystone_endpoint_run.log

az_domain=${1}

ifs=$IFS
IFS='.' arr=(${az_domain})
IFS=${ifs}

az_localaz=${arr[0]}
az_localdz=${arr[1]}
az_region=${az_localaz}"."${az_localdz}

v2v_gw_ip=${2}

. /root/adminrc
keystone service-list > keystone_service_list.temp
temp=`cat keystone_service_list.temp`
for i in {1..10}
do
    if [ -n "${temp}" ]; then
        break
    else
        . /root/adminrc
        keystone service-list > keystone_service_list.temp
        temp=`cat keystone_service_list.temp`
    fi
done

if [ -n "${temp}" ]; then
    continue
else
    exit 127
fi

cps_id=`awk -F "|" '{if($4~/cps/) print $2}' keystone_service_list.temp`
if [ -z "${cps_id}" ]; then
    sleep 0.5s
    cps_id=`keystone service-list | awk -F "|" '{if($4~/cps/) print $2}'`
fi


log_id=`awk -F "|" '{if($4~/ log /) print $2}' keystone_service_list.temp`
if [ -z "${log_id}" ]; then
    sleep 0.5s
    log_id=`keystone service-list | awk -F "|" '{if($4~/ log /) print $2}'`
fi

oam_id=`awk -F "|" '{if($4~/oam/) print $2}' keystone_service_list.temp`
if [ -z "${oam_id}" ]; then
    sleep 0.5s
    oam_id=`keystone service-list | awk -F "|" '{if($4~/oam/) print $2}'`
fi

volume_v2_id=`awk -F "|" '{if($4~/volumev2/) print $2}' keystone_service_list.temp`
if [ -z "${volume_v2_id}" ]; then
    sleep 0.5s
    volume_v2_id=`keystone service-list | awk -F "|" '{if($4~/volumev2/) print $2}'`
fi

upgrade_id=`awk -F "|" '{if($4~/upgrade/) print $2}' keystone_service_list.temp`
if [ -z "${upgrade_id}" ]; then
    sleep 0.5s
    upgrade_id=`keystone service-list | awk -F "|" '{if($4~/upgrade/) print $2}'`
fi

compute_id=`awk -F "|" '{if($4~/compute/) print $2}' keystone_service_list.temp`
if [ -z "${compute_id}" ]; then
    sleep 0.5s
    compute_id=`keystone service-list | awk -F "|" '{if($4~/compute/) print $2}'`
fi

backup_id=`awk -F "|" '{if($4~/backup/) print $2}' keystone_service_list.temp`
if [ -z "${backup_id}" ]; then
    sleep 0.5s
    backup_id=`keystone service-list | awk -F "|" '{if($4~/backup/) print $2}'`
fi

orchestration_id=`awk -F "|" '{if($4~/orchestration/) print $2}' keystone_service_list.temp`
if [ -z "${orchestration_id}" ]; then
    sleep 0.5s
    orchestration_id=`keystone service-list | awk -F "|" '{if($4~/orchestration/) print $2}'`
fi

info_collect_id=`awk -F "|" '{if($4~/collect/) print $2}' keystone_service_list.temp`
if [ -z "${info_collect_id}" ]; then
    sleep 0.5s
    info_collect_id=`keystone service-list | awk -F "|" '{if($4~/collect/) print $2}'`
fi

object_store_id=`awk -F "|" '{if($4~/object-store/) print $2}' keystone_service_list.temp`
if [ -z "${object_store_id}" ]; then
    sleep 0.5s
    object_store_id=`keystone service-list | awk -F "|" '{if($4~/object-store/) print $2}'`
fi

volume_id=`awk -F "|" '{if($4~/volume /) print $2}' keystone_service_list.temp`
if [ -z "${volume_id}" ]; then
    sleep 0.5s
    volume_id=`keystone service-list | awk -F "|" '{if($4~/volume /) print $2}'`
fi

network_id=`awk -F "|" '{if($4~/network/) print $2}' keystone_service_list.temp`
if [ -z "${network_id}" ]; then
    sleep 0.5s
    network_id=`keystone service-list | awk -F "|" '{if($4~/network/) print $2}'`
fi

metering_id=`awk -F "|" '{if($4~/metering/) print $2}' keystone_service_list.temp`
if [ -z "${metering_id}" ]; then
    sleep 0.5s
    metering_id=`keystone service-list | awk -F "|" '{if($4~/metering/) print $2}'`
fi

v2v_id=`awk -F "|" '{if($4~/ v2v /) print $2}' keystone_service_list.temp`
if [ -z "${metering_id}" ]; then
    sleep 0.5s
    v2v_id=`keystone service-list | awk -F "|" '{if($4~/v2v/) print $2}'`
fi

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${cps_id} --publicurl "'"https://cps.${az_domain}:443"'" --internalurl "'"https://cps.localdomain.com:8008"'" --adminurl "'"https://cps.${az_domain}:443"'"  >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${log_id} --publicurl "'"https://log.${az_domain}:443"'"  --internalurl "'"https://log.localdomain.com:8232"'" --adminurl "'"https://log.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${oam_id} --publicurl "'"https://oam.${az_domain}:443"'"  --internalurl "'"https://oam.localdomain.com:8200"'" --adminurl "'"https://oam.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${volume_v2_id} --publicurl "'"https://volume.${az_domain}:443/v2/'$(tenant_id)s'"'"  --internalurl "'"https://volume.localdomain.com:8776/v2/'$(tenant_id)'s"'" --adminurl "'"https://volume.${az_domain}:443/v2/'$(tenant_id)s'"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${upgrade_id} --publicurl "'"https://upgrade.${az_domain}:443"'"  --internalurl "'"https://upgrade.localdomain.com:8100"'" --adminurl "'"https://upgrade.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${compute_id} --publicurl "'"https://compute.${az_domain}:443/v2/'$(tenant_id)s'"'"  --internalurl "'"https://compute.localdomain.com:8001/v2/'$(tenant_id)s'"'" --adminurl "'"https://compute.${az_domain}:443/v2/'$(tenant_id)s'"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${backup_id} --publicurl "'"https://backup.${az_domain}:443"'"  --internalurl "'"https://backup.localdomain.com:8888"'" --adminurl "'"https://backup.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${orchestration_id} --publicurl "'"https://orchestration.${az_domain}:443/v1/'$(tenant_id)s'"'"  --internalurl "'"https://orchestration.localdomain.com:8700/v1/'$(tenant_id)s'"'" --adminurl "'"https://orchestration.${az_domain}:443/v1/'$(tenant_id)s'"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${info_collect_id} --publicurl "'"https://info-collect.${az_domain}:443"'"  --internalurl "'"https://info-collect.localdomain.com:8235"'" --adminurl "'"https://info-collect.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${object_store_id} --publicurl "'"https://object-store.${az_domain}:443/v1/AUTH_'$(tenant_id)s'"'"  --internalurl "'"http://object-store.localdomain.com:8006/v1/AUTH_'$(tenant_id)s'"'" --adminurl "'"http://object-store.${az_domain}:443/v1/AUTH_'$(tenant_id)s'"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${volume_id} --publicurl "'"https://volume.${az_domain}:443/v2/'$(tenant_id)s'"'"  --internalurl "'"https://volume.localdomain.com:8776/v2/'$(tenant_id)s'"'" --adminurl "'"https://volume.${az_domain}:443/v2/'$(tenant_id)s'"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${network_id} --publicurl "'"https://network.${az_domain}:443"'"  --internalurl "'"https://network.localdomain.com:8020"'" --adminurl "'"https://network.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo keystone endpoint-create --region ${az_region} --service ${metering_id} --publicurl "'"https://metering.${az_domain}:443"'"  --internalurl "'"https://metering.localdomain.com:8777"'" --adminurl "'"https://metering.${az_domain}:443"'" >> ${RUN_SCRIPT}

echo sleep 1s >> ${RUN_SCRIPT}

echo '#'keystone endpoint-create --region ${az_region} --service ${v2v_id} --publicurl "'"http://${v2v_gw_ip}:8090/"'"  --internalurl "'"http://${v2v_gw_ip}:8090/"'" --adminurl "'"http://${v2v_gw_ip}:8090/"'" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

temp=`cat ${RUN_LOG} | grep 'Authorization Failed'`
if [ -n "${temp}" ]; then
    exit 127
fi
