'''
@author: luobin
'''
import sys
from ceph import Ceph
from backend import Backend
from services import restart_component
from constant import CephConstant
import getopt
import os 
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = CURRENT_PATH+"/backup_az.log"

LOCAL_CEPH_PATH = CephConstant.LOCAL_CEPH_PATH
REMOTE_CEPH_PATH = CephConstant.REMOTE_CEPH_PATH

CEPH_CONF = CephConstant.CEPH_CONF
CEPH_KEYRING = CephConstant.CEPH_KEYRING

CEPH_BACKUP_CONF = CephConstant.CEPH_BACKUP_CONF
CEPH_BACKUP_KEYRING = CephConstant.CEPH_BACKUP_KEYRING

CEPH_USER = CephConstant.CEPH_USER
CEPH_KEYPAIR = CephConstant.CEPH_KEYPAIR

from constant import BackendConstant
CEPH_VOLUME_PREFIX = BackendConstant.CEPH_VOLUME_PREFIX

from constant import VolumeTypeConstant
VOLUME_TYPE_PREFIX = VolumeTypeConstant.VOLUME_TYPE_PREFIX


sys.path.append('/usr/bin/')
import log as LOG

def usage():
    print "backup_az.py usage:"
    print "--domain:              az_domain"
    print "--backup_domain:       backup_az_domain"
    print "--host:                ceph_host"
    print "--backup_host:         ceph_backup_host"
    
def backup_az(az_domain, backup_az_domain, ceph_host, backup_ceph_host):
    # get ceph conf and keyring
    LOG.info("connect to ceph: host=%s" % ceph_host)
    ceph = Ceph(ceph_host=ceph_host, ceph_user=CEPH_USER, ceph_key_file=CEPH_KEYPAIR)

    LOG.info("get %s from %s" % (CEPH_CONF, ceph_host))
    ceph.get_file(LOCAL_CEPH_PATH+"/"+CEPH_CONF, REMOTE_CEPH_PATH+"/"+CEPH_CONF)

    LOG.info("get %s from %s" % (CEPH_KEYRING, ceph_host))
    ceph.get_file(LOCAL_CEPH_PATH+"/"+CEPH_KEYRING, REMOTE_CEPH_PATH+"/"+CEPH_KEYRING)
    ceph.close()

    # get backup ceph conf and keyring
    LOG.info("connect to backup_ceph: host=%s" % backup_ceph_host)
    backup_ceph = Ceph(ceph_host=backup_ceph_host, ceph_user=CEPH_USER, ceph_key_file=CEPH_KEYPAIR)
    
    LOG.info("get %s from %s" % (CEPH_BACKUP_CONF, backup_ceph_host))
    backup_ceph.get_file(LOCAL_CEPH_PATH+"/"+CEPH_BACKUP_CONF, REMOTE_CEPH_PATH+"/"+CEPH_BACKUP_CONF)
    
    LOG.info("get %s from %s" % (CEPH_BACKUP_KEYRING, backup_ceph_host))
    backup_ceph.get_file(LOCAL_CEPH_PATH+"/"+CEPH_BACKUP_KEYRING, REMOTE_CEPH_PATH+"/"+CEPH_BACKUP_KEYRING)
    backup_ceph.close()

    backend = Backend()
    # update volume_backend_name
    volume_backend_name = CEPH_VOLUME_PREFIX+":"+az_domain+":"+backup_az_domain
    LOG.info("ceph storage backend update: volume_backend_name = %s" % volume_backend_name)
    backend.update_ceph_param("volume_backend_name", volume_backend_name)

    # update iscsi_server_ip
    LOG.info("ceph storage backend update:iscsi_server_ip=%s" % ceph_host)
    backend.update_ceph_param("iscsi_server_ip", ceph_host)
    # backend.commit()
    '''
    update_params = {}
    volume_backend_name = CEPH_VOLUME_PREFIX+":"+az_domain+":"+backup_az_domain
    update_params["volume_backend_name"] = volume_backend_name
    update_params["iscsi_server_ip"] = ceph_host
    backend.update_ceph_params(update_params)
    '''
    # set volume_type key
    # volume_type=VOLUME_TYPE_PREFIX+"@"+az_domain
    shell_file = CURRENT_PATH+"/script/volume_backend_name.sh"
    # os.system("/bin/bash " + shell_file + " " + volume_type + " " + volume_backend_name)
    os.system("/bin/bash " + shell_file + " " + az_domain + " " + backup_az_domain)

    # restart Service
    restart_component("cinder", "cinder-volume")
    restart_component("cinder", "cinder-backup")

def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], None, ["help", "domain=", "backup_domain=", "host=", "backup_host="])
    except getopt.GetoptError as e:
        usage()
        sys.exit(2)
    az_domain = None
    backup_az_domain = None
    ceph_host = None
    backup_ceph_host = None
    
    for param, val in opts:
        if param == "--domain":
            az_domain = val
        elif param == "--backup_domain":
            backup_az_domain = val
            
        elif param == "--host":
            ceph_host = val
        elif param == "--backup_host":
            backup_ceph_host = val
        
        elif param == "--help":
            usage()
            sys.exit(0)
        else:
            print "unhandled param"
            sys.exit(3)
    LOG.info("domain=%s, backup_domain=%s, host=%s, backup_host=%s" %
             (az_domain, backup_az_domain, ceph_host, backup_ceph_host))
    backup_az(az_domain, backup_az_domain, ceph_host, backup_ceph_host)
     
if __name__ == "__main__":
    LOG.init("ceph backup az")
    LOG.info('START to set ceph backup az...')
    argv = sys.argv
    main(argv)
    LOG.info('END set ceph backup az...')
