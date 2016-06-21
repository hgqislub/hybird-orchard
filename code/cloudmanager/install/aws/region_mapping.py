# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'


class RegionMapException(Exception):
    pass

__REGION_MAP = {"tokyo": "ap-northeast-1",
                "singapore": "ap-southeast-1",
                "sydney": "ap-southeast-2",
                "ireland": "eu-west-1",
                "sao-paulo": "sa-east-1",
                "virginia": "us-east-1",
                "california": "us-west-1",
                "oregon": "us-west-2",
                "frankfurt": "eu-central-1"}


def get_region_name_list():
    return __REGION_MAP.keys()


def get_region_id(region_name):
    if region_name in __REGION_MAP.keys():
        return __REGION_MAP[region_name]
    raise RegionMapException("get region id, region name: %s, no such region"
                             % region_name)


def get_region_name(region_id):
    for region_name in __REGION_MAP.keys():
        if region_id == __REGION_MAP[region_name]:
            return region_name
    raise RegionMapException("get region name, region id: %s, no such region"
                             % region_id)
