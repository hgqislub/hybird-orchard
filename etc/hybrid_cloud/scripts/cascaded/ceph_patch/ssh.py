'''
@author: luobin
'''
import paramiko
import os
from constant import SSHConstant

KNOWN_HOSTS_FILE = SSHConstant.KNOWN_HOSTS_FILE

class SSHError(Exception):
    pass

class SSH(object):
    def __init__(self, host, user, password=None, key_file=None):
        self.host = host
        self.user = user
        self.password = password
        self.key_file = key_file
        self._client = False
    
    def _get_client(self):
        try:
            if self.password == None and self.key_file == None:
                self._client = False
                pass
            elif self.password:
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._client.connect(hostname=self.host, username=self.user, password=self.password)
                self._client.load_host_keys(KNOWN_HOSTS_FILE)
                self._client.save_host_keys(KNOWN_HOSTS_FILE)
                return
            elif self.key_file:
                pkey = paramiko.RSAKey.from_private_key_file(self.key_file)
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._client.connect(hostname=self.host, username=self.user, pkey=pkey)
                self._client.load_host_keys(KNOWN_HOSTS_FILE)
                self._client.save_host_keys(KNOWN_HOSTS_FILE)
                return
        except Exception as e:
            self._client = False
            message = "Exception was raised during connect to %(user)s@%(host)s.Exception value is: %(exception)r"
            raise SSHError(message % {"exception": e,
                                      "host": self.host,
                                      "user": self.user})
    
    def get_file(self, remote_file, local_file, mode=None):
        self._get_client()
        if self._client:
            sftp = self._client.open_sftp()
            sftp.get(remote_file, local_file)
            if mode:
                os.chmod(local_file, mode)

    def close(self):
        if self._client:
            self._client.close()
            self._client = False
