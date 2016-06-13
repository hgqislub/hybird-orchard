#!/bin/bash
if [ $# != 4 ]; then
   echo "use: sh remove_cloud.sh domain proxy_id proxy_num api_ip"
   exit 1
fi

domain=${1}
proxy=${2}
proxy_num=${3}
ip=${4}
echo remove $domain $proxy $proxy_num

sh remove_aggregate.sh ${domain}
echo remove_aggregate.sh ${domain}

sh remove_cinder_service.sh ${domain}
echo remove_cinder_service.sh ${domain}

sh remove_neutron_agent.sh ${domain}
echo remove_neutron_agent.sh ${domain}

sh remove_neutron_agent.sh ${proxy}
echo remove_neutron_agent.sh ${proxy}

sh remove_keystone_endpoint.sh ${domain}
echo remove_keystone_endpoint.sh ${domain}

sh remove_proxy_host.sh ${proxy} $proxy_num
echo remove_proxy_host.sh ${proxy} $proxy_num

sh /home/hybrid_cloud/scripts/public/modify_dns_server_address.sh remove /${domain}/${ip}

echo "sh /home/hybrid_cloud/scripts/public/modify_dns_server_address.sh remove /${domain}/${ip}"
