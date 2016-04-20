import subprocess
import log

class vm_installer_vcenter(object):
    def __init__(self, ovf_name, vcenter_url, ds, user, pwd):
        self.ovf_name = ovf_name
        self.vcenter_url = vcenter_url
        self.ds = ds
        self.user = user
        self.pwd = pwd

    def _install_with_poweron(self, vm_name):
        create_vm_cmd = 'ovftool -ds=%s --powerOn --name="%s" %s vi://%s:%s@%s' % (self.ds, vm_name, self.ovf_name, self.user, self.pwd, self.vcenter_url)
        #create_vm_cmd = 'ovftool -ds=%s --powerOn  %s vi://%s:%s@%s' % (self.ds, self.ovf_name, self.user, self.pwd, self.vcenter_url)
        result = subprocess.call(create_vm_cmd, shell=True)
        if result != 0:
            log.error("[install_with_poweron]create vm failed.")
            return -1
        return 0

    def _uninstll(self, vm_name):
        return 0

