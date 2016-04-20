'''
@author: luobin
'''
from ssh import SSH

class Ceph():
    def __init__(self, ceph_host, ceph_user, ceph_password=None, ceph_key_file=None):
        self.ceph_host = ceph_host
        self.ceph_user = ceph_user
        self.ceph_password = ceph_password
        self.ceph_key_file = ceph_key_file
        self._ssh = self._get_ssh()
    
    def _get_ssh(self):
        return SSH(host=self.ceph_host, user=self.ceph_user, password=self.ceph_password, key_file=self.ceph_key_file)
    
    def get_file(self, local_file, remote_file):
        self._ssh.get_file(remote_file, local_file)
    
    def close(self):
        self._ssh.close()
