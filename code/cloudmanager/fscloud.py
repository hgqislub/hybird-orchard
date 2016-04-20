class FsCloud(object):
    def __init__(self, cloud_id, azName, dc,cloud_proxy=None,keystone_url=None,associate_user_id=None,
                associate_admin_id=None,associate_service_id=None,access=None,is_api_vpn=None,fs_vpn_eip=None,
                fs_vpn_username=None,fs_vpn_password=None,fs_api_subnet_id=None,fs_api_vpn_ip=None,
                fs_tunnel_subnet_id=None,fs_tunnel_vpn_ip=None, cascaded_ip=None,
                cascaded_user_name=None,cascaded_user_password=None):
        self.cloud_id = cloud_id
        self.azName = azName
        self.dc = dc
        self.cloud_proxy = cloud_proxy
        self.keystone_url =keystone_url
        self.associate_user_id = associate_user_id
        self.associate_admin_id =associate_admin_id
        self.associate_service_id = associate_service_id
        self.access = access
        self.is_api_vpn = is_api_vpn
        self.fs_vpn_eip = fs_vpn_eip
        self.fs_vpn_username = fs_vpn_username
        self.fs_vpn_password = fs_vpn_password
        self.fs_api_subnet_id = fs_api_subnet_id
        self.fs_api_vpn_ip = fs_api_vpn_ip
        self.fs_tunnel_subnet_id = fs_tunnel_subnet_id
        self.fs_tunnel_vpn_ip = fs_tunnel_vpn_ip  
        
        self.cascaded_ip = cascaded_ip
        self.cascaded_user_name = cascaded_user_name
        self.cascaded_user_password = cascaded_user_password     

    def get_vpn_conn_name(self):
        vpn_conn_name = {"api_conn_name": self.cloud_id + '-api',
                         "tunnel_conn_name": self.cloud_id + '-tunnel'}
        return vpn_conn_name

    