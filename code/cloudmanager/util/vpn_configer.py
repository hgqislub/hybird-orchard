# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import time
from heat.openstack.common import log as logging

from vpn import VPN
import commonutils

LOG = logging.getLogger(__name__)


class VpnConfiger(object):
    def __init__(self, host_ip, user, password):
        self.host_ip = host_ip
        self.user = user
        self.password = password
        self.add_conns = []
        self.delete_conns = []

    def register_add_conns(self, tunnel_name, left_public_ip,
                           left_subnet, right_public_ip, right_subnet):
        conn = {"tunnel_name": tunnel_name,
                "left_public_ip": left_public_ip,
                "left_subnet": left_subnet,
                "right_public_ip": right_public_ip,
                "right_subnet": right_subnet}
        self.add_conns.append(conn)

    def register_remove_conns(self, conn_name):
        self.delete_conns.append(conn_name)

    def do_config(self):
        # check status
        start_time = time.time()
        LOG.info("check vpn status, vpn: %s" % self.host_ip)
        commonutils.check_host_status(self.host_ip, self.user, self.password,
                                      retry_time=500, interval=1)

        LOG.info("vpn is ready, vpn: %s" % self.host_ip)
        LOG.info("start config vpn, vpn: %s, add_conns: %s"
                    % (self.host_ip, self.add_conns))
        # add_conn
        vpn = VPN(public_ip=self.host_ip, user=self.user,
                  pass_word=self.password)

        for conn in self.add_conns:
            try:
                vpn.add_tunnel(tunnel_name=conn["tunnel_name"],
                               left=conn["left_public_ip"],
                               left_subnet=conn["left_subnet"],
                               right=conn["right_public_ip"],
                               right_subnet=conn["right_subnet"])
            except Exception as e:
                LOG.error("add conn error, vpn: %s, conn: %s, error: %s"
                             % (self.host_ip, conn, e.message))
        LOG.info("add conns success, vpn: %s, conns: %s"
                    % (self.host_ip, self.add_conns))

        # delete conns
        for conn in self.delete_conns:
            try:
                vpn.remove_tunnel(conn)
            except Exception as e:
                LOG.error("delete conn error, vpn: %s, conn: %s, error: %s"
                             % (self.host_ip, conn, e.message))
        LOG.info("delete conns success, vpn: %s, conns: %s"
                    % (self.host_ip, self.delete_conns))

        try:
            vpn.restart_ipsec_service()
        except Exception as e:
            LOG.error("restart ipsec error, vpn: %s, error: %s"
                         % (self.host_ip, e.message))

        cost_time = time.time() - start_time
        LOG.info("config vpn success, vpn: %s, cost time: %d"
                    % (self.host_ip, cost_time))
