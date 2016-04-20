#!/bin/bash
src_base_path=$(cd `dirname $0`; pwd)/code

cp /etc/cinder/others/cfg_template/cinder-volume.json /etc/cinder/others/cfg_template/cinder-volume.json.bak
cp ${src_base_path}/etc/cinder/others/cfg_template/cinder-volume.json /etc/cinder/others/cfg_template/cinder-volume.json

cp /etc/nova/others/cfg_template/nova-compute.json /etc/nova/others/cfg_template/nova-compute.json.bak
cp ${src_base_path}/etc/nova/others/cfg_template/nova-compute.json /etc/nova/others/cfg_template/nova-compute.json

cp /etc/nova/nova.conf.sample /etc/nova/nova.conf.sample.bak
cp ${src_base_path}/etc/nova/nova.conf.sample /etc/nova/nova.conf.sample

sed -i "/\"compute_driver\"/c\"compute_driver\": \"nova.virt.aws.AwsAgentlessDriver\"," /etc/nova/nova.json

dos2unix ${src_base_path}/../add_router.sh
sh ${src_base_path}/../add_router.sh
exit 0