# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'
import sys
sys.path.append('..')

import os
import time
import sshclient
from exception import *
 

from heat.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def check_host_status(host, user, password, retry_time=100, interval=1):
    LOG.info("check host status, host: %s" % host)
    if host is None:
        raise SSHCommandFailure(host=host, command=cmd, error="host is None")
    ssh = sshclient.SSH(host=host, user=user, password=password)
    for i in range(retry_time):
        try:
            ssh.execute("ls")
            LOG.info("host is ok, host: %s" % host)
            return True
        except Exception:
            time.sleep(interval)
            continue
    LOG.error("check host status failed, host = % s" % host)
    raise CheckHostStatusFailure(host=host)


def do_execute_cmd_without_stdout(host, user, password, cmd):
    LOG.debug("execute ssh command, host = %s, cmd = %s" % (host, cmd))
    if host is None:
        raise SSHCommandFailure(host=host, command=cmd, error="host is None")
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        operate_result = ssh.execute(cmd)
    except Exception as e:
        LOG.error("execute ssh command failed: host: %s, cmd: %s, error: %s"
                     % (ssh.host, cmd, e.message))
        raise SSHCommandFailure(host=ssh.host, command=cmd, error=e.message)
    finally:
        ssh.close()

    exit_code = operate_result[0]
    if exit_code == 0:
        return True
    else:
        LOG.error(
            "execute ssh command failed: host = %s, cmd = %s, reason = %s"
            % (ssh.host, cmd, operate_result[2]))
        raise SSHCommandFailure(
            host=ssh.host, command=cmd, error=operate_result[2])

def execute_cmd_without_stdout(host, user, password, cmd, retry_time=1, interval=1):
    for i in range(retry_time):
        try:
            do_execute_cmd_without_stdout(host, user, password, cmd)
            return True
        except Exception:
            time.sleep(interval)
            continue
    LOG.error("execute ssh command failed, host = % s" % host)
    raise CheckHostStatusFailure(host=host)

def do_execute_cmd_with_stdout(host, user, password, cmd):
    LOG.debug("execute ssh command, host = %s, cmd = %s" % (host, cmd))
    if host is None:
        raise SSHCommandFailure(host=host, command=cmd, error="host is None")
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        operate_result = ssh.execute(cmd)
    except Exception as e:
        LOG.error(
            "execute ssh command failed: host = %s, cmd = %s, reason = %s"
            % (ssh.host, cmd, e.message))
        raise SSHCommandFailure(host=ssh.host, command=cmd, error=e.message)
    finally:
        ssh.close()

    exit_code = operate_result[0]
    if exit_code == 0:
        return operate_result[1]
    else:
        LOG.error(
            "execute ssh command failed: host = %s, cmd = %s, reason = %s"
            % (ssh.host, cmd, operate_result[2]))
        raise SSHCommandFailure(
            host=ssh.host, command=cmd, error=operate_result[2])

def execute_cmd_with_stdout(host, user, password, cmd, retry_time=1, interval=1):
    for i in range(retry_time):
        try:
            do_execute_cmd_with_stdout(host, user, password, cmd)
            return True
        except Exception:
            time.sleep(interval)
            continue
    LOG.error("execute ssh command failed, host = % s" % host)
    raise CheckHostStatusFailure(host=host)

def scp_file_to_host(host, user, password, file_name, local_dir, remote_dir):
    LOG.debug("spc file to host, host = %s, file_name = %s, "
                 "local_dir = %s, remote_dir = %s"
                 % (host, file_name, local_dir, remote_dir))
    ssh = sshclient.SSH(host=host, user=user, password=password)
    try:
        ssh.put_file(os.path.join(local_dir, file_name),
                     remote_dir + "/" + file_name)
    except (sshclient.SSHError, sshclient.SSHTimeout) as e:
        LOG.error(
            "spc file to host failed, host = %s, "
            "file_name = %s, local_dir = %s, remote_dir = %s, reason = %s"
            % (ssh.host, file_name, local_dir, remote_dir, e.message))
        raise ScpFileToHostFailure(host=ssh.host, file_name=file_name,
                                   local_dir=local_dir,
                                   remote_dir=remote_dir,
                                   error=e.message)
    finally:
        ssh.close()

    return True
