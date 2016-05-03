
import sys
sys.path.append('..')

from heat.openstack.common import log as logging
import threading
import os


_hws_access_cloud_data_file = os.path.join("/home/hybrid_cloud/data/hws",
                                           "hws_access_cloud_install.data")
_hws_access_cloud_data_file_lock = threading.Lock()

LOG=logging.getLogger(__name__)

class HwsCloudInfo(utils.CloudInfo):
    def __init__(self):
        pass

    def initialize(self, cloud_params, install_info, proxy_info, installer):
        pass