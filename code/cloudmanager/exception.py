# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from heat.openstack.common import log as logging

LOG=logging.getLogger(__name__)


class CloudManagerException(Exception):
    """Base CloudManager Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception as e:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))

                message = self.msg_fmt

        super(CloudManagerException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full NovaException message, (see __init__)
        return self.args[0]


class ReadEnvironmentInfoFailure(CloudManagerException):
    msg_fmt = "failed to read environment info, error: %(error)s"


class ReadProxyDataFailure(CloudManagerException):
    msg_fmt = "failed to read proxy data, error: %(error)s"


class InstallAWSAccessCloudFailure(CloudManagerException):
    msg_fmt = "failed to install aws access cloud, error: %(error)s"


class SSHCommandFailure(CloudManagerException):
    msg_fmt = "failed to execute ssh command : " \
              "host: %(host)s, command: %(command)s, error: %(error)s"


class ScpFileToHostFailure(CloudManagerException):
    msg_fmt = "spc file to host failed, host: %(host)s," \
              " file_name: %(file_name)s, local_dir: %(local_dir)s," \
              " remote_dir: %(remote_dir)s, error: %(error)s"


class PersistCloudInfoFailure(CloudManagerException):
    msg_fmt = "failed to Persist cloud info, error: %(error)s"


class ReadCloudInfoFailure(CloudManagerException):
    msg_fmt = "failed to read cloud info, error: %(error)s"


class CheckHostStatusFailure(CloudManagerException):
    msg_fmt = "check host status failed, host: %(host)s"


class ConfigCascadedHostFailure(CloudManagerException):
    msg_fmt = "failed to config cascaded host: %(error)s"


class ConfigProxyFailure(CloudManagerException):
    msg_fmt = "failed to config proxy: %(error)s"

if __name__ == '__main__':
    e = ReadEnvironmentInfoFailure(error="test")
    print e
