from clouds import *
"""
cloud = {
            "availability_zone": string,      # hybrid availability zone
            "region": string,              # region name
            "cloud_type": "OpenStack",
            "cloud_info": {
                "cloud_urlinfo":{
                    "domainname": string      # "openstack.huawei.com"
                 },
                "vpninfo": {
                    "public_ip": string,
                    "api_ip": string,
                    "api_subnet": string,
                    "data_ip": string,
                    "data_subnet": string,
                }
           }
      }
"""



{
    "aws": {
        "availability_zone": None,
        "region": None,
        "cloud_type": "",
        "cloud_info": {
            "aws_availabilityzone": None,
            "accesskey": None,
            "secretkey": None,
        }
    }, 

    "vcloud": {
        "availability_zone": None,
        "region": None,
        "cloud_type": "vCloud",
        "cloud_info": {
            "vpninfo": {
                "public_ip": None,
                "api_ip": None,
                "api_subnet": None,
                "data_ip": None,
                "data_subnet": None,
            },
            "vCloud_info": {
                "org": None,
                "vdc": None,
                "username": None,
                "password": None,
                "external_id": None
            }
        }
    }, 
    "openstack": {
        "availability_zone": None,
        "region": None,
        "cloud_type": "vCloud",
        "cloud_info": {
            "vpninfo": {
                "public_ip": None,
                "api_ip": None,
                "api_subnet": None,
                "data_ip": None,
                "data_subnet": None,
            },
            "cloud_urlinfo": {
                "domainname":None
            }
        }
    }
}

def test_front_to_back():
    for cloud_type, v in {
        "aws": {
            "availability_zone": "availability_zone",
            "region": "region",
            "cloud_type": "aws",
            "cloud_info": {
                "aws_availabilityzone": "aws_availabilityzone",
                "accesskey": "accesskey",
                "secretkey": "secretkey",
            }
        }, 

        "vcloud": {
            "availability_zone": "availability_zone",
            "region": "region",
            "cloud_type": "vCloud",
            "cloud_info": {
                "vpninfo": {
                    "public_ip": "public_ip",
                    "api_ip": "api_ip",
                    "api_subnet": "api_subnet",
                    "data_ip": "data_ip",
                    "data_subnet": "data_subnet",
                },
                "vCloud_info": {
                    "org": "org",
                    "vdc": "vdc",
                    "username": "username",
                    "password": "password",
                    "external_id": "external_id"
                }
            }
        }, 
        "openstack": {
            "availability_zone": "availability_zone",
            "region": "region",
            "cloud_type": "openstack",
            "cloud_info": {
                "vpninfo": {
                    "public_ip": "public_ip",
                    "api_ip": "api_ip",
                    "api_subnet": "api_subnet",
                    "data_ip": "data_ip",
                    "data_subnet": "data_subnet",
                },
                "cloud_urlinfo": {
                    "domainname": "domainname"
                }
            }
        }
        }.items():
        ov = v
        v = translate_front_back(v)
        # print cloud_type, "front to back", v
        v = translate_front_back(v)
        # print cloud_type, "back to front ", v, "###", v == ov
        assert v==ov, cloud_type

test_front_to_back()
