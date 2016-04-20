# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import boto.ec2
import boto.ec2.networkinterface as ec2_net_interface
import boto.vpc
from retry_decorator import RetryDecorator
from cloud_manager_exception import *


class AWSInterface(object):
    def __init__(self, subnet_id, private_ip_address=None):
        self.subnet_id = subnet_id
        self.private_ip_address = private_ip_address


class AWSInstaller(object):
    def __init__(self, access_key_id, secret_key_id, region, az):
        self.access_key_id = access_key_id
        self.secret_key_id = secret_key_id
        self.region = region
        self.az = az
        self.ec2_conn = boto.ec2.connect_to_region(
            self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_key_id)
        self.vpc_conn = boto.vpc.connect_to_region(
            self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_key_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="create vpc"))
    def create_vpc(self, cidr_block):
        vpc = self.vpc_conn.create_vpc(cidr_block)
        return vpc

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=UninstallCascadingFailed(
                        current_step="delete vpc"))
    def delete_vpc(self, vpc_id):
        return self.vpc_conn.delete_vpc(vpc_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="create subnet"))
    def create_subnet(self, vpc_id, cidr_block):
        subnet = self.vpc_conn.create_subnet(vpc_id, cidr_block,
                                             availability_zone=self.az)
        return subnet.id

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=UninstallCascadingFailed(
                        current_step="delete subnet"))
    def delete_subnet(self, subnet_id):
        return self.vpc_conn.delete_subnet(subnet_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="create vm"))
    def create_vm(self, image_name, instance_type, *interfaces_list):
        ec2_interfaces = []
        dev_index = 0
        for interface in interfaces_list:
            ec2_interface = ec2_net_interface.NetworkInterfaceSpecification(
                subnet_id=interface.subnet_id,
                private_ip_address=interface.private_ip_address,
                device_index=dev_index)
            ec2_interfaces.append(ec2_interface)
            dev_index += 1

        ec2_interfaces_coll = ec2_net_interface.NetworkInterfaceCollection(
            *ec2_interfaces)

        image_id = self.query_image_id(image_name)
        instance = self.ec2_conn.run_instances(
            image_id, instance_type=instance_type,
            network_interfaces=ec2_interfaces_coll)
        return instance.instances[0]

    @RetryDecorator(max_retry_count=10,
                    raise_exception=InstallCascadingFailed(
                        current_step="allocate elastic IP"))
    def allocate_elastic_address(self):
        return self.ec2_conn.allocate_address()

    @RetryDecorator(max_retry_count=50, init_sleep_time=3,
                    raise_exception=InstallCascadingFailed(
                        current_step="associate elastic IP"))
    def associate_elastic_address(self, eip, network_interface_id):
        return self.ec2_conn.associate_address(
            public_ip=eip.public_ip,
            allocation_id=eip.allocation_id,
            network_interface_id=network_interface_id)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=None)
    def terminate_instance(self, *instance_id):
        instance_ids = []
        for instance in instance_id:
            instance_ids.append(instance)
        return self.ec2_conn.terminate_instances(instance_ids)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=None)
    def disassociate_elastic_address(self, public_ip):
        return self.ec2_conn.disassociate_address(public_ip=public_ip)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=None)
    def release_elastic_address(self, allocation_id):
        return self.ec2_conn.release_address(allocation_id=allocation_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="create internet gateway"))
    def create_internet_gateway(self):
        gateway = self.vpc_conn.create_internet_gateway()
        return gateway.id

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="attach internet gateway"))
    def attach_internet_gateway(self, gateway_id, vpc_id):
        return self.vpc_conn.attach_internet_gateway(gateway_id, vpc_id)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=UninstallCascadingFailed(
                        current_step="detach internet gateway"))
    def detach_internet_gateway(self, gateway_id, vpc_id):
        return self.vpc_conn.detach_internet_gateway(gateway_id, vpc_id)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=UninstallCascadingFailed(
                        current_step="delete internet gateway"))
    def delete_internet_gateway(self, gateway_id):
        return self.vpc_conn.delete_internet_gateway(gateway_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="get all route tables"))
    def get_all_route_tables(self, vpc_id):
        return self.vpc_conn.get_all_route_tables(filters={"vpc_id": vpc_id})

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="create route tables"))
    def create_route_table(self, vpc_id):
        return self.vpc_conn.create_route_table(vpc_id)

    @RetryDecorator(max_retry_count=20,
                    raise_exception=InstallCascadingFailed(
                        current_step="create route"))
    def create_route(self, table_id, destination_cidr, interface_id=None,
                     gateway_id=None):
        return self.vpc_conn.create_route(table_id, destination_cidr,
                                          interface_id=interface_id,
                                          gateway_id=gateway_id)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=UninstallCascadingFailed(
                        current_step="delete route table"))
    def delete_route_table(self, table_id):
        return self.vpc_conn.delete_route_table(table_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="query image id"))
    def query_image_id(self, image_name):
        image_list = self.ec2_conn.get_all_images(filters={"name": image_name})
        return image_list[0].id

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="create none dhcp options"))
    def create_none_dhcp_options(self):
        return self.vpc_conn.create_dhcp_options()

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="associate dhcp options"))
    def associate_dhcp_options(self, dhcp_options_id, vpc_id):
        return self.vpc_conn.associate_dhcp_options(dhcp_options_id, vpc_id)

    @RetryDecorator(max_retry_count=100, init_sleep_time=3,
                    raise_exception=UninstallCascadingFailed(
                        current_step="delete dhcp options"))
    def delete_dhcp_options(self, dhcp_options_id):
        return self.vpc_conn.delete_dhcp_options(dhcp_options_id)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="disable sdcheck"))
    def disable_instance_sdcheck(self, instance_id):
        return self.ec2_conn.modify_instance_attribute(
            instance_id=instance_id,
            attribute="sourceDestCheck",
            value="false")

    def disable_network_interface_sdcheck(self, network_interface_id):
        return self.ec2_conn.modify_network_interface_attribute(
            interface_id=network_interface_id,
            attr="sourceDestCheck",
            value="false")

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="get all security groups"))
    def get_all_security_groups(self, vpc_id):
        return self.ec2_conn.get_all_security_groups(filters={"vpc_id": vpc_id})

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="add security to vpc"))
    def add_security_to_vpc(self, vpc_id, cidr):
        sec_groups = self.ec2_conn.get_all_security_groups(
            filters={"vpc_id": vpc_id})
        for sec_group in sec_groups:
            sec_group.authorize(ip_protocol="-1", cidr_ip=cidr)

    @RetryDecorator(max_retry_count=50,
                    raise_exception=InstallCascadingFailed(
                        current_step="assign private ip addresses"))
    def assign_private_ip_addresses(self, network_interface_id,
                                    private_ip_addresses):
        return self.ec2_conn.assign_private_ip_addresses(
            network_interface_id=network_interface_id,
            private_ip_addresses=private_ip_addresses)
