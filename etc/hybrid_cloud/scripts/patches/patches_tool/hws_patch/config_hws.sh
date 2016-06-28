#!/bin/sh
NOVA_SAMPLE_CONFIG_FILE=/etc/nova/nova.json.sample
NOVA_CONFIG_FILE=/etc/nova/nova.json
PERSONALITY_PATH=/home/userdata.txt

project_id=${1}
vpc_id=${2}
subnet_id=${3}
service_region=${4}
resource_region=${5}
ecs_host=${6}
ims_host=${7}
evs_host=${8}
vpc_host=${9}
gong_yao=${10}
si_yao=${11}
tunnel_cidr=${12}
route_gw=${13}
personality_path=${PERSONALITY_PATH}
rabbit_host_ip=${14}
security_group_vpc=${15}
volume_type=SATA
service_protocol=https
service_port=443
volume_driver=cinder.volume.drivers.hws.HWSDriver
volume_manager=cinder.volume.manager.VolumeManager

config_nova(){
    sed -i "s#%project_id%#${project_id}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%vpc_id%#${vpc_id}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%subnet_id%#${subnet_id}#g" ${NOVA_CONFIG_FILE}

    sed -i "s#%service_region%#${service_region}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%resource_region%#${resource_region}#g" ${NOVA_CONFIG_FILE}

    sed -i "s#%ecs_host%#${ecs_host}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%ims_host%#${ims_host}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%evs_host%#${evs_host}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%vpc_host%#${vpc_host}#g" ${NOVA_CONFIG_FILE}

    sed -i "s#%gong_yao%#${gong_yao}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%si_yao%#${si_yao}#g" ${NOVA_CONFIG_FILE}

    sed -i "s#%tunnel_cidr%#${tunnel_cidr}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%route_gw%#${route_gw}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%personality_path%#${personality_path}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%rabbit_host_ip%#${rabbit_host_ip}#g" ${NOVA_CONFIG_FILE}
    sed -i "s#%security_group_vpc%#${security_group_vpc}#g" ${NOVA_CONFIG_FILE}

    source /root/adminrc
    cps host-template-instance-operate --action stop --service nova nova-compute
    cps host-template-instance-operate --action start --service nova nova-compute
}

config_cinder_volume(){
    source /root/adminrc
    cps template-ext-params-update --parameter default.volume_driver=${volume_driver} --service cinder cinder-volume
    cps template-ext-params-update --parameter default.volume_manager=${volume_manager} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.project_id=${project_id} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.gong_yao=${gong_yao} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.si_yao=${si_yao} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.volume_type=${volume_type} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.service_protocol=${service_protocol} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.service_port=${service_port} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.ecs_host=${ecs_host} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.evs_host=${evs_host} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.ims_host=${ims_host} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.vpc_host=${vpc_host} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.service_region=${service_region} --service cinder cinder-volume
    cps template-ext-params-update --parameter hws.resource_region=${resource_region} --service cinder cinder-volume
    cps commit

    cps host-template-instance-operate --action stop --service cinder cinder-volume
    cps host-template-instance-operate --action start --service cinder cinder-volume
}

if [ $# != 15 ]; then
    echo "Usage: sh $0 project_id vpc_id subnet_id service_region resource_region ecs_host
    ims_host evs_host vpc_host gong_yao si_yao tunnel_cidr route_gw rabbit_host_ip security_group_vpc"
    exit 1
fi

cp ${NOVA_SAMPLE_CONFIG_FILE} ${NOVA_CONFIG_FILE}
config_nova
config_cinder_volume

