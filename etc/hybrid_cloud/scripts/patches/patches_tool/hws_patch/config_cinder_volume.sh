#!/bin/sh
source /root/adminrc
cps template-ext-params-update --parameter default.volume_driver=cinder.volume.drivers.hws.HWSDriver --service cinder cinder-volume
cps template-ext-params-update --parameter default.volume_manager=cinder.volume.manager.VolumeManager --service cinder cinder-volume
cps template-ext-params-update --parameter hws.project_id=91d957f0b92d48f0b184c26975d2346e --service cinder cinder-volume
cps template-ext-params-update --parameter hws.gong_yao=YKTA94WTIDZNDUVCY4QI --service cinder cinder-volume
cps template-ext-params-update --parameter hws.si_yao=DHSYAC8LZVB5TCEEX39XMXNJ6BOAGA0UTJA7PCT3 --service cinder cinder-volume
cps template-ext-params-update --parameter hws.volume_type=SATA --service cinder cinder-volume
cps template-ext-params-update --parameter hws.service_protocol=https --service cinder cinder-volume
cps template-ext-params-update --parameter hws.service_port=443 --service cinder cinder-volume
cps template-ext-params-update --parameter hws.ecs_host=ecs.cn-north-1.myhwclouds.com.cn --service cinder cinder-volume
cps template-ext-params-update --parameter hws.evs_host=evs.cn-north-1.myhwclouds.com.cn --service cinder cinder-volume
cps template-ext-params-update --parameter hws.ims_host=ims.cn-north-1.myhwclouds.com.cn --service cinder cinder-volume
cps template-ext-params-update --parameter hws.vpc_host=vpc.cn-north-1.myhwclouds.com.cn --service cinder cinder-volume
cps template-ext-params-update --parameter hws.service_region=cn-north-1 --service cinder cinder-volume
cps template-ext-params-update --parameter hws.resource_region=cn-north-1a --service cinder cinder-volume
cps commit
    