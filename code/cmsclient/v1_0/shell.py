# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
# All Rights Reserved.
#
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

from __future__ import print_function

import argparse
import copy
import datetime
import getpass
import locale
import logging
import os
import sys
import time

from oslo.utils import encodeutils
from oslo.utils import strutils
from oslo.utils import timeutils
import six

from cmsclient import exceptions
from cmsclient.i18n import _
from cmsclient.common import cliutils
from cmsclient.common import uuidutils
from cmsclient import utils


logger = logging.getLogger(__name__)

###### clouds
def _print_cloud_list(clouds, show_cloud_info=False):

    headers = [
        'ID',
        'Cloud Type',
        'Availability Zone',
        'Region',
    ]

    formatters = {}
    if show_cloud_info:
        headers.append('Cloud Info')

    utils.print_list(clouds, headers, formatters)

def _print_cloud(cloud):
    info = cloud._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info, wrap=80)

def _find_cloud(cs, cloud):
    """Get a cloud by name, ID."""
    try:
        return utils.find_resource(cs.clouds, cloud)
    except exceptions.NotFound as e:
        raise e


@utils.arg('--cloud-info',
        dest='cloud_info',
        action='store_true',
        default=False,
        help=_('Get cloud info of echo cloud.'))
def do_cloud_list(cs, args):
    """Print a list of available 'clouds'."""
    clouds = cs.clouds.list()
    _print_cloud_list(clouds, args.cloud_info)


@utils.arg('cloud',
    metavar='<cloud-id>',
    help=_("Name or ID of the cloud to delete"))
def do_cloud_delete(cs, args):
    """Delete a specific cloud"""
    cloudid = _find_cloud(cs, args.cloud)
    cs.clouds.delete(cloudid)
    _print_cloud_list([cloudid])


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
def do_cloud_show(cs, args):
    """Show details about the given cloud."""
    cloud = _find_cloud(cs, args.cloud)
    _print_cloud(cloud)


@utils.arg('cloud_type',
     metavar='<cloud_type>',
     help=_("Cloud type of the new cloud."))
@utils.arg('availability_zone',
     metavar='<availability_zone>',
     help=_("Availability_zone of the new cloud"))
@utils.arg('region',
     metavar='<region>',
     help=_("Region name of the new cloud"))

## cloud_urlinfo
@utils.arg('--domainname',
     metavar='<domainname>',
     help=_("Domain name of the cloud (required for openstack)"))

## vpn info
@utils.arg('--public-ip',
     metavar='<public-ip>', 
     dest='public_ip',
     help=_("public ip of the cloud (required for openstack/vCloud)"))
@utils.arg('--api-ip',
     metavar='<api-ip>', 
     dest='api_ip',
     help=_("Api ip of the cloud (required for openstack/vCloud)"))
@utils.arg('--api-subnet',
     metavar='<api-subnet>',
     dest='api_subnet',
     help=_("Api subnet of the cloud (required for openstack/vCloud)"))
@utils.arg('--data-ip',
     metavar='<data-ip>',
     dest='data_ip',
     help=_("Data(tunnel) ip of the cloud (required for openstack/vCloud)"))
@utils.arg('--data-subnet',
     metavar='<data-subnet>',
     dest='data_subnet',
     help=_("Data(tunnel) subnet of the cloud (required for openstack/vCloud)"))

## vcloud info
@utils.arg('--org',
     help=_("Org of the cloud (required for vCloud)"))
@utils.arg('--vdc',
     help=_("Vdc of the cloud (required for vCloud)"))
@utils.arg('--username',
     help=_("Username of the cloud (required for vCloud)"))
@utils.arg('--password',
     help=_("Password of the cloud (required for vCloud)"))
@utils.arg('--external-id',
     dest='external_id',
     help=_("External id of the cloud (required for vCloud)"))

# aws cloud info
@utils.arg('--aws-availabilityzone',
     dest='aws_availabilityzone',
     help=_("Aws availability zone of the aws cloud (required for aws)"))
@utils.arg('--accesskey',
     help=_("Accesskey zone of the aws cloud (required for aws)"))
@utils.arg('--secretkey',
     help=_("Secretkey zone of the aws cloud (required for aws)"))
def do_cloud_create(cs, args):
    """Create a new cloud"""

    info = {


            # common
            "cloud_type" : args.cloud_type, 
            "availability_zone" : args.availability_zone, 
            "region" : args.region, 

            # openstack
            "domainname" : args.domainname, 

            # vpn info, openstack/vcloud
            "public_ip" : args.public_ip, 
            "api_ip" : args.api_ip, 
            "api_subnet" : args.api_subnet, 
            "data_ip" : args.data_ip, 
            "data_subnet" : args.data_subnet, 

            # vcloud info
            "org" : args.org,
            "vdc" : args.vdc,
            "username" : args.username,
            "password" : args.password,
            "external_id" : args.external_id,

            # aws cloud info

            "aws_availabilityzone" : args.aws_availabilityzone,
            "accesskey" : args.accesskey,
            "secretkey" : args.secretkey
        }
    f = cs.clouds.create(**info)
    _print_cloud_list([f])

@utils.arg('id',
     metavar='<id>',
     help=_("ID of the cloud"))
@utils.arg('--cloud-type',
     dest='cloud_type',
     metavar='<cloud_type>',
     help=_("Cloud type of the new cloud."))
@utils.arg('--availability-zone',
     dest='availability_zone',
     metavar='<availability_zone>',
     help=_("Availability_zone of the new cloud"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the new cloud"))

## cloud_urlinfo
@utils.arg('--domainname',
     metavar='<domainname>',
     help=_("Domain name of the cloud (required for openstack)"))

## vpn info
@utils.arg('--public-ip',
     metavar='<public-ip>', 
     dest='public_ip',
     help=_("public ip of the cloud (required for openstack/vCloud)"))
@utils.arg('--api-ip',
     metavar='<api-ip>', 
     dest='api_ip',
     help=_("Api ip of the cloud (required for openstack/vCloud)"))
@utils.arg('--api-subnet',
     metavar='<api-subnet>',
     dest='api_subnet',
     help=_("Api subnet of the cloud (required for openstack/vCloud)"))
@utils.arg('--data-ip',
     metavar='<data-ip>',
     dest='data_ip',
     help=_("Data(tunnel) ip of the cloud (required for openstack/vCloud)"))
@utils.arg('--data-subnet',
     metavar='<data-subnet>',
     dest='data_subnet',
     help=_("Data(tunnel) subnet of the cloud (required for openstack/vCloud)"))

## vcloud info
@utils.arg('--org',
     help=_("Org of the cloud (required for vCloud)"))
@utils.arg('--vdc',
     help=_("Vdc of the cloud (required for vCloud)"))
@utils.arg('--username',
     help=_("Username of the cloud (required for vCloud)"))
@utils.arg('--password',
     help=_("Password of the cloud (required for vCloud)"))
@utils.arg('--external-id',
     dest='external_id',
     help=_("External id of the cloud (required for vCloud)"))

# aws cloud info
@utils.arg('--aws-availabilityzone',
     dest='aws_availabilityzone',
     help=_("Aws availability zone of the aws cloud (required for aws)"))
@utils.arg('--accesskey',
     help=_("Accesskey zone of the aws cloud (required for aws)"))
@utils.arg('--secretkey',
     help=_("Secretkey zone of the aws cloud (required for aws)"))
def do_cloud_update(cs, args):
    info = {


            # common
            "cloud_type" : args.cloud_type, 
            "availability_zone" : args.availability_zone, 
            "region" : args.region, 

            # openstack
            "domainname" : args.domainname, 

            # vpn info, openstack/vcloud
            "public_ip" : args.public_ip, 
            "api_ip" : args.api_ip, 
            "api_subnet" : args.api_subnet, 
            "data_ip" : args.data_ip, 
            "data_subnet" : args.data_subnet, 

            # vcloud info
            "org" : args.org,
            "vdc" : args.vdc,
            "username" : args.username,
            "password" : args.password,
            "external_id" : args.external_id,

            # aws cloud info

            "aws_availabilityzone" : args.aws_availabilityzone,
            "accesskey" : args.accesskey,
            "secretkey" : args.secretkey
        }
    cs.clouds.update(args.id, **info)

###### users
def _print_user_list(users):

    headers = [
        'ID',
        'Name',
        'Region',
        'Description',
    ]

    formatters = {}

    utils.print_list(users, headers, formatters)

def _print_user(user):
    info = user._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_user(cs, user):
    """Get a user by name, ID."""
    try:
        return utils.find_resource(cs.users, user)
    except exceptions.NotFound as e:
        raise e


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
def do_user_list(cs, args):
    """Print a list of available 'users'."""
    cs.users.set_cloud(args.cloud)
    users = cs.users.list()
    _print_user_list(users)


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('user',
    metavar='<user>',
    help=_("Name or ID of the user to delete"))
def do_user_delete(cs, args):
    """Delete a specific user"""
    cs.users.set_cloud(args.cloud)
    userid = _find_user(cs, args.user)
    cs.users.delete(userid)
    _print_user_list([userid])


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('user',
     metavar='<user>',
     help=_("Name or ID of user"))
def do_user_show(cs, args):
    """Show details about the given user."""
    cs.users.set_cloud(args.cloud)
    user = _find_user(cs, args.user)
    _print_user(user)


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('name',
     metavar='<name>',
     help=_("Name of the new user"))
@utils.arg('password',
     metavar='<password>',
     help=_("Password of the new user"))
@utils.arg('--description',
     metavar='<description>',
     help=_("Description of the user (optional)"))
def do_user_create(cs, args):
    """Create a new user"""
    cs.users.set_cloud(args.cloud)
    f = cs.users.create(name=args.name, password=args.password, description=args.description)
    _print_user_list([f])

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('id',
     metavar='<id>',
     help=_("ID of the user"))
@utils.arg('--name',
     metavar='<name>',
     help=_("Name of the user (optional)"))
@utils.arg('--password',
     metavar='<password>',
     help=_("Password of the user (optional)"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the user (optional)"))
@utils.arg('--description',
     metavar='<description>',
     help=_("Description of the user (optional)"))
def do_user_update(cs, args):
    cs.users.set_cloud(args.cloud)
    cs.users.update(args.id, name=args.name, 
                    password=args.password,
                    region=args.region, 
                    description=args.description)

###### project association 
def _print_association_list(name, associations):

    headers = [
        'ID', 
        'H' + name.capitalize(),
         name.capitalize(),
        'Region',
    ]
    if name.lower() == 'project':
        headers.append('Userid')

    utils.print_list(associations, headers)

def _print_association(association):
    info = association._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_association(cs, association):
    """Get a association by name, ID."""
    try:
        return utils.find_resource(cs.associations, association)
    except exceptions.NotFound as e:
        raise e

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
def do_project_association_list(cs, args):
    """Print a list of available 'project_associations'."""
    cs.associations.set_cloud(args.cloud)
    name="project"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('project_association',
    metavar='<project_association>',
    help=_("Name or ID of the project_association to delete"))
def do_project_association_delete(cs, args):
    """Delete a specific project_association"""
    cs.associations.set_cloud(args.cloud)
    name="project"
    cs.associations.set_name(name)
    association = _find_association(cs, args.project_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('project_association',
     metavar='<project_association>',
     help=_("Name or ID of project_association"))
def do_project_association_show(cs, args):
    """Show details about the given project_association."""
    cs.associations.set_cloud(args.cloud)
    name="project"
    cs.associations.set_name(name)
    association = _find_association(cs, args.project_association)
    _print_association(association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('id',
     metavar='<id>',
     help=_("Id of the project association"))
@utils.arg('--hproject',
     metavar='<hproject>',
     help=_("Cascading project id of the project association "))
@utils.arg('--project',
     metavar='<project>',
     help=_("Cascaded project id of the project association"))
@utils.arg('--userid',
     metavar='<userid>',
     help=_("Userid created by user-create"))
def do_project_association_update(cs, args):
    """Update a project association"""
    cs.associations.set_cloud(args.cloud)
    name="project"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, hproject=args.hproject, project=args.project, 
                                 userid=args.userid)
    _print_association_list(name, [f])

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('hproject',
     metavar='<hproject>',
     help=_("Cascading project id of the new project association"))
@utils.arg('project',
     metavar='<project>',
     help=_("Cascaded project id of the new project association"))
@utils.arg('userid',
     metavar='<userid>',
     help=_("Userid created by user-create"))
def do_project_association_create(cs, args):
    """Create a new project_association"""
    cs.associations.set_cloud(args.cloud)
    name="project"
    cs.associations.set_name(name)
    info = {
            "hproject" : args.hproject, 
            "project": args.project, 
            "userid": args.userid
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])

###### flavor association 

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
def do_flavor_association_list(cs, args):
    """Print a list of available 'flavor_associations'."""
    cs.associations.set_cloud(args.cloud)
    name="flavor"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('flavor_association',
    metavar='<flavor_association>',
    help=_("Name or ID of the flavor_association to delete"))
def do_flavor_association_delete(cs, args):
    """Delete a specific flavor_association"""
    cs.associations.set_cloud(args.cloud)
    name="flavor"
    cs.associations.set_name(name)
    association = _find_association(cs, args.flavor_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('flavor_association',
     metavar='<flavor_association>',
     help=_("Name or ID of flavor_association"))
def do_flavor_association_show(cs, args):
    """Show details about the given flavor_association."""
    cs.associations.set_cloud(args.cloud)
    name="flavor"
    cs.associations.set_name(name)
    association = _find_association(cs, args.flavor_association)
    _print_association(association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('id',
     metavar='<id>',
     help=_("Id of the flavor association"))
@utils.arg('--hflavor',
     metavar='<hflavor>',
     help=_("Cascading flavor id of the flavor association "))
@utils.arg('--flavor',
     metavar='<flavor>',
     help=_("Cascaded flavor id of the flavor association"))
def do_flavor_association_update(cs, args):
    """Update a flavor association"""
    cs.associations.set_cloud(args.cloud)
    name="flavor"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, hflavor=args.hflavor, flavor=args.flavor)
    _print_association_list(name, [f])

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('hflavor',
     metavar='<hflavor>',
     help=_("Cascading flavor id of the new flavor association"))
@utils.arg('flavor',
     metavar='<flavor>',
     help=_("Cascaded flavor id of the new flavor association"))
def do_flavor_association_create(cs, args):
    """Create a new flavor_association"""
    cs.associations.set_cloud(args.cloud)
    name="flavor"
    cs.associations.set_name(name)
    info = {
            "hflavor" : args.hflavor, 
            "flavor": args.flavor
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])

###### image association 

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
def do_image_association_list(cs, args):
    cs.associations.set_cloud(args.cloud)
    """Print a list of available 'image_associations'."""
    name="image"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('image_association',
    metavar='<image_association>',
    help=_("Name or ID of the image_association to delete"))
def do_image_association_delete(cs, args):
    """Delete a specific image_association"""
    cs.associations.set_cloud(args.cloud)
    name="image"
    cs.associations.set_name(name)
    association = _find_association(cs, args.image_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('image_association',
     metavar='<image_association>',
     help=_("Name or ID of image_association"))
def do_image_association_show(cs, args):
    """Show details about the given image_association."""
    cs.associations.set_cloud(args.cloud)
    name="image"
    cs.associations.set_name(name)
    association = _find_association(cs, args.image_association)
    _print_association(association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('id',
     metavar='<id>',
     help=_("Id of the image association"))
@utils.arg('--himage',
     metavar='<himage>',
     help=_("Cascading image id of the image association "))
@utils.arg('--image',
     metavar='<image>',
     help=_("Cascaded image id of the image association"))
def do_image_association_update(cs, args):
    """Update a image association"""
    cs.associations.set_cloud(args.cloud)
    name="image"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, himage=args.himage, image=args.image)
    _print_association_list(name, [f])

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('himage',
     metavar='<himage>',
     help=_("Cascading image id of the new image association"))
@utils.arg('image',
     metavar='<image>',
     help=_("Cascaded image id of the new image association"))
def do_image_association_create(cs, args):
    """Create a new image_association"""
    cs.associations.set_cloud(args.cloud)
    name = "image"
    cs.associations.set_name(name)
    info = {
            "himage" : args.himage, 
            "image": args.image, 
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])

###### network association 

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
def do_network_association_list(cs, args):
    cs.associations.set_cloud(args.cloud)
    """Print a list of available 'network_associations'."""
    name="network"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('network_association',
    metavar='<network_association>',
    help=_("Name or ID of the network_association to delete"))
def do_network_association_delete(cs, args):
    """Delete a specific network_association"""
    cs.associations.set_cloud(args.cloud)
    name="network"
    cs.associations.set_name(name)
    association = _find_association(cs, args.network_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('network_association',
     metavar='<network_association>',
     help=_("Name or ID of network_association"))
def do_network_association_show(cs, args):
    """Show details about the given network_association."""
    cs.associations.set_cloud(args.cloud)
    name="network"
    cs.associations.set_name(name)
    association = _find_association(cs, args.network_association)
    _print_association(association)

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('id',
     metavar='<id>',
     help=_("Id of the network association"))
@utils.arg('--hnetwork',
     metavar='<hnetwork>',
     help=_("Cascading network id of the network association "))
@utils.arg('--network',
     metavar='<network>',
     help=_("Cascaded network id of the network association"))
def do_network_association_update(cs, args):
    """Update a network association"""
    cs.associations.set_cloud(args.cloud)
    name="network"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, hnetwork=args.hnetwork, network=args.network)
    _print_association_list(name, [f])

@utils.arg('cloud',
     metavar='<cloud-id>',
     help=_("ID of cloud"))
@utils.arg('hnetwork',
     metavar='<hnetwork>',
     help=_("Cascading network id of the new network association"))
@utils.arg('network',
     metavar='<network>',
     help=_("Cascaded network id of the new network association"))
def do_network_association_create(cs, args):
    """Create a new network_association"""
    cs.associations.set_cloud(args.cloud)
    name = "network"
    cs.associations.set_name(name)
    info = {
            "hnetwork" : args.hnetwork, 
            "network": args.network, 
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])


def do_version_list(cs, args):
    """List all API versions."""
    result = cs.versions.list()
    columns = ["Id", "Status", "Updated"]
    utils.print_list(result, columns)
