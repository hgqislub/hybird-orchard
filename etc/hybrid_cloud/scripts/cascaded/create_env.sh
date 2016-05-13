#!/usr/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
EVN_FILE=/root/env.sh
ADMINRC=/root/adminrc

cascading_domain=${1}
az_domain=${2}

ifs=$IFS
IFS='.' arr=(${az_domain})
IFS=${ifs}

az_localaz=${arr[0]}
az_localdz=${arr[1]}
az_region=${az_localaz}"."${az_localdz}

cat > ${EVN_FILE} <<CONFIG
export OS_AUTH_URL=https://identity.${cascading_domain}:443/identity/v2.0
export OS_USERNAME=cloud_admin
export OS_TENANT_NAME=admin
export OS_REGION_NAME=${az_region}
export NOVA_ENDPOINT_TYPE=publicURL
export CINDER_ENDPOINT_TYPE=publicURL
export OS_ENDPOINT_TYPE=publicURL
export OS_VOLUME_API_VERSION=2
export OS_PASSWORD=FusionSphere123
export CPS_USERNAME=cps_admin
export CPS_PASSWORD=FusionSphere123

CONFIG

cp ${EVN_FILE} ${ADMINRC}
