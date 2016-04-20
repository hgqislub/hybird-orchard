# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from commonutils import *
from constant import *

from heat.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class VPN(object):

    def __init__(self, public_ip, user, pass_word):
        """Initialize VPN.
        :param public_ip: VPN public ip
        :param user: VPN ssh user
        :param pass_word: VPN ssh password
        """
        self.public_ip = public_ip
        self.user = user
        self.pass_word = pass_word

    def add_tunnel(self, tunnel_name, left, left_subnet, right, right_subnet):
        LOG.info("add a new tunnel, vpn = % s, tunnel = % s"
                    % (self.public_ip, tunnel_name))

        execute_cmd_without_stdout(
            host=self.public_ip,
            user=self.user,
            password=self.pass_word,
            cmd='cd %(dir)s; sh %(script)s '
                '%(tunnel_name)s %(left)s %(left_subnet)s '
                '%(right)s %(right_subnet)s'
                % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR,
                   "script": VpnConstant.ADD_TUNNEL_SCRIPT,
                   "tunnel_name": tunnel_name,
                   "left": left, "left_subnet": left_subnet,
                   "right": right, "right_subnet": right_subnet})
        return True

    def remove_tunnel(self, tunnel_name):
        LOG.info("remove tunnel, vpn = % s, tunnel = % s"
                    % (self.public_ip, tunnel_name))

        execute_cmd_without_stdout(
            host=self.public_ip,
            user=self.user,
            password=self.pass_word,
            cmd='cd %(dir)s; sh %(script)s %(tunnel_name)s'
                % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR,
                   "script": VpnConstant.REMOVE_TUNNEL_SCRIPT,
                   "tunnel_name": tunnel_name})
        return True

    def list_tunnel(self):
        LOG.info("list tunnel, vpn = % s"
                    % self.public_ip)
        tunnel_list = execute_cmd_with_stdout(
            host=self.public_ip,
            user=self.user,
            password=self.pass_word,
            cmd='cd %(dir)s; sh %(script)s'
                % {"dir": VpnConstant.REMOTE_SCRIPTS_DIR,
                   "script": VpnConstant.LIST_TUNNEL_SCRIPT})
        return tunnel_list.strip("\n").split(',')

    def restart_ipsec_service(self):
        LOG.info("restart ipsec service, vpn = % s"
                    % self.public_ip)
        execute_cmd_without_stdout(
            host=self.public_ip,
            user=self.user,
            password=self.pass_word,
            cmd="service ipsec restart")
        return True

    def up_tunnel(self, *tunnel_name):
        LOG.info("up tunnel, vpn = % s"
                    % self.public_ip)
        cmd = ""
        for name in tunnel_name:
            cmd += "ipsec auto --up %s;" % name
        execute_cmd_without_stdout(
            host=self.public_ip,
            user=self.user,
            password=self.pass_word,
            cmd=cmd)
        return True
