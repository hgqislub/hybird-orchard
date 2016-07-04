#!/bin/sh
NOVA_SAMPLE_CONFIG_FILE=/etc/nova/nova.json.sample
NOVA_CONFIG_FILE=/etc/nova/nova.json
PERSONALITY_PATH=/home/userdata.txt
config_hws(){
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

}

if [ $# != 15 ]; then
    echo "Usage: sh $0 project_id vpc_id subnet_id service_region resource_region ecs_host
    ims_host evs_host vpc_host gong_yao si_yao tunnel_cidr route_gw rabbit_host_ip security_group_vpc"
    exit 1
fi

cp ${NOVA_SAMPLE_CONFIG_FILE} ${NOVA_CONFIG_FILE}
config_hws ${1} ${2} ${3} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11} ${12} ${13} ${14} ${15}
