import os

from heat.openstack.common import log as logging
import json

LOG = logging.getLogger(__name__)

def read_conf(file_path):
    with open(file_path, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)

def write_conf(file_path, data):
    with open(file_path, 'w+') as fd:
        fd.write(json.dumps(data, indent=4))
        return True