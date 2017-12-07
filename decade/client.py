#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Curtis Yu
@contact: cuyu@splunk.com
@since: 06/12/2017
"""
import stat
import docker
import os
import paramiko
from common import tar_cz, tar_xz


class Client(object):
    """
    A client to wrap both ssh and docker client
    """

    def __init__(self, host, ssh_username=None, ssh_password=None, ssh_port=22):
        if ssh_username and ssh_password:
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh_client.connect(host, ssh_port, ssh_username, ssh_password)
            self._sftp = paramiko.SFTPClient.from_transport(self._ssh_client.get_transport())
            self._docker_client = None
        else:
            self._ssh_client = None
            self._docker_client = docker.from_env()
            self._docker_container = self._docker_client.containers.get(host)

    def execute(self, command):
        if self._ssh_client:
            # Return (stdin, stdout, stderr) which are file-like objects
            stdin, stdout, stderr = self._ssh_client.exec_command(command)
            return stdin, stdout, stderr
        else:
            # Return generator or str
            return self._docker_container.exec_run(command)

    def send_files(self, local_path, remote_path):
        if self._ssh_client:
            self._sftp.put(local_path, remote_path)
        else:
            data = tar_cz(local_path)
            self._docker_container.put_archive(os.path.dirname(remote_path), data)

    def fetch_files(self, remote_path, local_path):
        assert os.path.exists(local_path)

        if self._ssh_client:
            if stat.S_ISDIR(self._sftp.stat(remote_path).st_mode):
                self._ssh_fetch_folder(remote_path, os.path.join(local_path, os.path.basename(remote_path)))
            else:
                self._sftp.get(remote_path, local_path)
        else:
            response, _ = self._docker_container.get_archive(remote_path)
            tar_xz(response.data, local_path)

    def _ssh_fetch_folder(self, remote_path, local_path):
        if not os.path.exists(local_path):
            os.mkdir(local_path)

        for f in self._sftp.listdir(remote_path):
            if stat.S_ISDIR(self._sftp.stat(os.path.join(remote_path, f)).st_mode):
                self._ssh_fetch_folder(os.path.join(remote_path, f), local_path)
            else:
                self._sftp.get(os.path.join(remote_path, f), os.path.join(local_path, f))
