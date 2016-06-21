# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import region_mapping


class AwsCloud(object):

    def __init__(self, cloud_id, access_key, secret_key,
                 region_name, az, az_alias,
                 cascaded_domain, cascaded_eip, vpn_eip, cloud_proxy=None,
                 driver_type="agentleass", access=True, with_ceph=True):
        self.cloud_id = cloud_id
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.az = az
        self.az_alias = az_alias
        self.cascaded_domain = cascaded_domain
        self.cascaded_eip = cascaded_eip
        self.vpn_eip = vpn_eip
        self.cloud_proxy = cloud_proxy
        self.driver_type = driver_type
        self.access = access
        self.with_ceph = with_ceph

    def get_vpn_conn_name(self):
        vpn_conn_name = {"api_conn_name": self.cloud_id + '-api',
                         "tunnel_conn_name": self.cloud_id + '-tunnel'}
        return vpn_conn_name

    def get_region_id(self):
        return region_mapping.get_region_id(self.region_name)
