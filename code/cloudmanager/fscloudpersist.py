from fscloud import FsCloud
from environmentinfo import *
from commonutils import *
import threading


def fs_cloud_2_dict(obj):
    result = {}
    result.update(obj.__dict__)
    return result

def dict_2_fs_cloud(fs_dict):
    #fs_cloud = FsCloud(cloud_id=fs_dict.get("cloud_id"),azName=fs_dict.get('azName'),dc=fs_dict.get('dc'),)
    fs_cloud = FsCloud(**fs_dict)
    return fs_cloud

fs_cloud_data_file = os.path.join("/home/hybrid_cloud/data",
                                  "fs_access_cloud.data")
fs_cloud_data_file_lock = threading.Lock()

class FsCloudDataHandler(object):
    def __init__(self):
        pass

    def list_fs_clouds(self):
        cloud_dicts = self.__read_fs_cloud_info__()
        return cloud_dicts.keys()

    def get_fs_cloud(self, cloud_id):
        cloud_dicts = self.__read_fs_cloud_info__()
        if cloud_id in cloud_dicts.keys():
            return dict_2_fs_cloud(cloud_dicts[cloud_id])
        else:
            return None

    def delete_fs_cloud(self, cloud_id):
        fs_cloud_data_file_lock.acquire()
        try:
            cloud_dicts = self.__read_fs_cloud_info__()
            cloud_dicts.pop(cloud_id)
            self.__write_aws_cloud_info__(cloud_dicts)
        except Exception as e:
            logger.error("delete fs cloud data file error, "
                         "cloud_id: %s, error: %s"
                         % (cloud_id, e.message))
        finally:
            fs_cloud_data_file_lock.release()

    def add_fs_cloud(self, fs_cloud):
        fs_cloud_data_file_lock.acquire()
        try:
            cloud_dicts = self.__read_fs_cloud_info__()
            dict_temp = fs_cloud_2_dict(fs_cloud)
            cloud_dicts[fs_cloud.cloud_id] = dict_temp
            self.__write_aws_cloud_info__(cloud_dicts)
        except Exception as e:
            logger.error("add fs cloud data file error, "
                         "fs cloud: %s, error: %s"
                         % (fs_cloud, e.message))
        finally:
            fs_cloud_data_file_lock.release()

    @staticmethod
    def __read_fs_cloud_info__():
        if not os.path.exists(fs_cloud_data_file):
            logger.error("read %s : No such file." % fs_cloud_data_file)
            cloud_dicts = {}
        else:
            with open(fs_cloud_data_file, 'r+') as fd:
                cloud_dicts = json.loads(fd.read())
        return cloud_dicts

    @staticmethod
    def __write_aws_cloud_info__(cloud_dicts):
        with open(fs_cloud_data_file, 'w+') as fd:
            fd.write(json.dumps(cloud_dicts, indent=4))
