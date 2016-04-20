#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import os
import time

import boto.ec2
import boto.vpc


class HyperNodeManager(object):
    # TODO (snapiri): we also have these in hypernode_installer.py
    #                 should move them into a single (uniform) location
    # Default names for the security groups
    _hns_sg_name = 'hns-sg'
    _vms_sg_name = 'vms-sg'
    _hn_subnet_name = 'Hypernode_Subnet'
    _vm_subnet_name = 'VM_Subnet'
    _route_table_name = 'HyperNode route table'

    @staticmethod
    def _timeout(delta):
        t = os.times()[-1]
        return lambda: os.times()[-1] - t > delta

    def __init__(self, access_key_id, secret_key_id, region, vpc_id):
        self.ec2_conn = boto.ec2.connect_to_region(
            region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key_id)

        self.vpc_conn = boto.vpc.connect_to_region(
            region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key_id)

        self._vpc_id = vpc_id

    def _get_subnets_with_filters(self, filterz,
                                  allow_none=True,
                                  allow_multi=True):
        """
        Finds a subnet using a filter

        :param filterz: dictionary of filters
        :type filterz: ``dict``
        :param allow_none: do not throw exception if no matches are found
        :type allow_none: ``bool``
        :param allow_multi: do not throw exception if more than one result
        :type allow_multi: ``bool``
        :returns: all subnets matching the filters
        :rtype: ``list`` of :class:`EC2NetworkSubnet`
        :raises: :class:`Exception`
        """
        subnets = self.vpc_conn.get_all_subnets(filters=filterz)
        # If the subnet exists, return it
        if not allow_multi and len(subnets) > 1:
            raise Exception('Too many networks match the '
                            'filter: %s' % (filterz,))
        if not allow_none and len(subnets) == 0:
            raise Exception('No subnet matches filter: %s' % (filterz,))
        return subnets

    def _get_subnet_by_name(self, subnet_name, allow_none=True):
        """
        Finds a subnet by Name if exists

        :param subnet_name: Name of the subnet
        :type subnet_name: ``str``
        :param allow_none: Allow empty list to be returned
        :returns: the network with the supplied ID
        :rtype: :class:`EC2NetworkSubnet`
        :raises: :class:`Exception`
        """
        filterz = {'tag:Name': subnet_name,
                   'vpc-id': self._vpc_id}
        subnets = self._get_subnets_with_filters(filterz, allow_none=allow_none,
                                                 allow_multi=False)
        if len(subnets) == 0:
            return None
        return subnets[0]

    def _delete_subnet(self, subnet_id):
        """
        Deletes a subnet

        :param subnet_id: The ID of the subnet
        :type subnet_id: ``str``
        :returns: True on success, False otherwise
        :rtype: ``boolean``
        """

        # Delete the subnet
        return self.vpc_conn.delete_subnet(subnet_id=subnet_id)

    def _get_all_hypernodes(self):
        """
        Returns a list of all hypernodes in the VPC

        :returns: All hypernodes in the VPC
        :rtype: ``list`` of ``boto.ec2.instance.Instance``
        """

        # Find all VMs with the tag is_hypernode: True
        return self.ec2_conn.get_only_instances(
            filters={'tag:is_hypernode': True, 'vpc-id': self._vpc_id})

    def _terminate_nodes(self, nodes):
        """
        Terminates multiple VMs

        :param nodes: List of the VMs to terminate
        :type nodes: ``list`` of ``boto.ec2.instance.Instance``
        :returns: A list of the instances terminated
        :rtype: ``list``
        """

        # Terminate the VMs
        node_ids = [node.id for node in nodes]
        return self.ec2_conn.terminate_instances(instance_ids=node_ids)

    def _wait_for_nodes_to_terminate(self, hypernodes):
        # Iterate over the VMs and wait for them to terminate
        # List of AWS state_code values:
        # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
        terminated_state = 48
        timeout = 120
        iteration_sleep_time = 30
        end_marker = object()

        nodes = collections.deque(hypernodes)
        nodes.append(end_marker)

        # The whole process should not take more than two minutes
        has_timed_out = HyperNodeManager._timeout(timeout)
        while len(nodes) > 1 and not has_timed_out():
            node = nodes.pop()
            if node != end_marker:
                if node.state_code != terminated_state:
                    nodes.append(self.ec2_conn.get_only_instances(
                        instance_ids=[node.id]))
            else:
                time.sleep(iteration_sleep_time)
                nodes.append(node)
        # END_MARKER is always in the queue
        return len(nodes) == 1

    def _get_route_table(self):
        """
        Finds the HN route table for our VPC

        :returns: A route table object
        :rtype: ``???``
        """

        # Find route table
        tables = self.vpc_conn.get_all_route_tables(
            filters={'tag:Name': self._route_table_name,
                     'vpc-id': self._vpc_id})
        if len(tables) > 0:
            return tables[0]
        return None

    def _delete_route_table(self, route_table_id):
        """
        Deletes a route table

        :param route_table_id: The ID of the route table
        :type route_table_id: ``str``
        :returns: True on success, False otherwise
        :rtype: ``boolean``
        """

        # Delete the route table
        return self.vpc_conn.delete_route_table(route_table_id=route_table_id)

    def get_security_group(self, group_name):
        """
        fetches a security group by its name

        :param group_name: the name of the security group
        :type group_name: ``str``
        :returns: the security group if it exists
        :rtype: :class:`EC2SecurityGroup`
        :raises: :class:`Exception`
        """
        groups = self.ec2_conn.get_all_security_groups(
            filters={'tag:Name': group_name, 'vpc-id': self._vpc_id})
        if len(groups) > 0:
            return groups[0]
        return None

    def _get_security_groups(self):
        """
        Returns the HN security_groups for the VPC

        :returns: the security groups
        :rtype: ``list`` of ``???``
        """

        group_names = (self._hns_sg_name, self._vms_sg_name)
        # Find security groups
        groups = []
        for name in group_names:
            group = self.ec2_conn.get_all_security_groups(
                filters={'group-name': name,
                         'vpc-id': self._vpc_id})
            if len(group) > 0:
                groups.append(group[0])
        return groups

    def _delete_security_groups(self, security_groups):
        """
        Deletes security groups

        :param security_groups: The security groups
        :type security_groups: ``list`` of ``??``
        :returns: True on success, False otherwise
        :rtype: ``boolean``
        """

        sg_ids = [group.id for group in security_groups]
        # First remove cross-references between the groups
        for group in security_groups:
            for rule in group.rules:
                for grant in rule.grants:
                    if grant.group_id and grant.group_id in sg_ids:
                        self.ec2_conn.revoke_security_group(
                            group_id=group.id,
                            src_security_group_group_id=grant.group_id,
                            ip_protocol=rule.ip_protocol,
                            from_port=rule.from_port,
                            to_port=rule.to_port)
        rc = True
        for group in security_groups:
            if not self.ec2_conn.delete_security_group(group_id=group.id):
                rc = False
        return rc

    def start_remove_all(self, tenant_id=None):
        """
        Removes all hypernodes. If the security groups and routing tables are
        not used, remove them as well

        :param tenant_id:  ID of the current tenant (Currently must be None)
        :type tenant_id: ``str``
        :returns: True on success, False otherwise
        :rtype: ``boolean``
        :raises: :class:`Exception'
         """
        try:
            # Find the VM subnet
            vm_subnet = self._get_subnet_by_name(self._vm_subnet_name,
                                                 allow_none=False)
            hn_subnet = self._get_subnet_by_name(self._hn_subnet_name,
                                                 allow_none=False)
            route_table = self._get_route_table()
            nodes = self._get_all_hypernodes()
            security_groups = self._get_security_groups()

            # Terminate all relevant hypernodes
            self._terminate_nodes(nodes)

            # Wait for the nodes to terminate
            self._wait_for_nodes_to_terminate(nodes)

            # Remove VM and HN subnets if possible
            self._delete_subnet(vm_subnet.id)
            self._delete_subnet(hn_subnet.id)

            # Remove relevant route tables
            self._delete_route_table(route_table.id)

            # Remove security groups
            self._delete_security_groups(security_groups)

            # Remove VM and HN subnets if possible
            # self._delete_subnet(vm_subnet.id)
            # self._delete_subnet(hn_subnet.id)

        except Exception as e:
            print 'HyperNodeInstaller.start_remove_all: Exception: %s' % str(e)
