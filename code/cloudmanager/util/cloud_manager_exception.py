# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'


class CloudManagerException(Exception):
    """Base HybridCloudaaS Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "Hybrid_Cloud_aa_S base exception."

    def __init__(self, **kwargs):
        self.kwargs = kwargs

        try:
            message = self.msg_fmt % kwargs
        except KeyError:
            message = self.msg_fmt

        super(CloudManagerException, self).__init__(message)

    def format_message(self):
        return self.args[0]


class InstallCascadingFailed(CloudManagerException):
    msg_fmt = "failed to install cascading openstack, " \
              "current step: %(current_step)s."


class UninstallCascadingFailed(CloudManagerException):
    msg_fmt = "failed to uninstall cascading openstack, " \
              "current step: %(current_step)s."

class InstallCascadedFailed(CloudManagerException):
    msg_fmt = "failed to install cascading openstack, " \
              "current step: %(current_step)s."


class UninstallCascadedFailed(CloudManagerException):
    msg_fmt = "failed to uninstall cascading openstack, " \
              "current step: %(current_step)s."

class SSHCommandFailure(CloudManagerException):
    msg_fmt = "failed to execute ssh command : " \
              "host: %(host)s, command: %(command)s, error: %(error)s"


class CheckHostStatusFailure(CloudManagerException):
    msg_fmt = "check host status failed, host: %(host)s"


class ScpFileToHostFailure(CloudManagerException):
    msg_fmt = "spc file to host failed, host: %(host)s," \
              " file_name: %(file_name)s, local_dir: %(local_dir)s," \
              " remote_dir: %(remote_dir)s, error: %(error)s"


