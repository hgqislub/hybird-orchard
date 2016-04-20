'''
@author: luobin
'''
class CephConstant(object):
    LOCAL_CEPH_PATH = "/etc/ceph"
    REMOTE_CEPH_PATH = "/etc/ceph"

    CEPH_CONF = "ceph.conf"
    CEPH_KEYRING = "ceph.client.cinder.keyring"

    CEPH_BACKUP_CONF = "ceph-backup.conf"
    CEPH_BACKUP_KEYRING = "ceph.client.cinder-backup.keyring"

    CEPH_USER = "ceph"
    CEPH_KEYPAIR = "/home/ceph-keypair.pem"

class BackendConstant(object):
    BACKEND_NAME = "multi-backends"
    CEPH_STORAGE_BACKEND = "rbd"
    CEPH_VOLUME_PREFIX = "HYBRID"
    
class VolumeTypeConstant(object):
    VOLUME_TYPE_PREFIX = "hybrid"

class SSHConstant(object):
    KNOWN_HOSTS_FILE = "/root/.ssh/known_hosts"
