#!/bin/bash
openstack_api_subnet=162.3.0.0/16
aws_api_gw=172.29.15.254
openstack_tunnel_subnet=172.28.48.0/20
aws_tunnel_gw=172.29.143.254

ip route show | grep ${openstack_api_subnet} && ip route del ${openstack_api_subnet}
ip route show | grep ${openstack_tunnel_subnet} && ip route del ${openstack_tunnel_subnet}

ip route add ${openstack_api_subnet} via ${aws_api_gw}
ip route add ${openstack_tunnel_subnet} via ${aws_tunnel_gw}

ip route show table external_api | grep ${openstack_api_subnet} && ip route del table external_api ${openstack_api_subnet}
ip route add table external_api ${openstack_api_subnet} via ${aws_api_gw}

