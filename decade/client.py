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
from logger import setup_logger
from colorama import Fore

_LOGGER = setup_logger('Client', color=Fore.CYAN)


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
        _LOGGER.info('executing command: {0}'.format(command))
        if self._ssh_client:
            # Return (stdin, stdout, stderr) which are file-like objects
            stdin, stdout, stderr = self._ssh_client.exec_command(command)
            stdout = ''.join(stdout.readlines())
            _LOGGER.info('stdout: \n{0}'.format(stdout))
            return stdin, stdout, stderr
        else:
            # Return generator or str
            result = self._docker_container.exec_run(command)
            if isinstance(result, str):
                stdout = result
            else:
                stdout = ''
                for line in result:
                    stdout += line + '\n'
            _LOGGER.info('stdout: \n{0}'.format(stdout))
            return result

    def send_files(self, local_path, remote_path):
        _LOGGER.info('sending files from {0} (local) to {1} (remote)'.format(local_path, remote_path))
        if self._ssh_client:
            if os.path.isdir(local_path):
                self._ssh_send_folder(local_path, remote_path)
            else:
                self._sftp.put(local_path, remote_path)
        else:
            data = tar_cz(local_path)
            self._docker_container.put_archive(os.path.dirname(remote_path), data)

    def _ssh_send_folder(self, local_path, remote_path):
        self._ssh_mkdir(remote_path, ignore_existing=True)

        for item in os.listdir(local_path):
            if os.path.isfile(os.path.join(local_path, item)):
                self._sftp.put(os.path.join(local_path, item), '%s/%s' % (remote_path, item))
            else:
                self._ssh_mkdir('%s/%s' % (remote_path, item), ignore_existing=True)
                self._ssh_send_folder(os.path.join(local_path, item), '%s/%s' % (remote_path, item))

    def _ssh_mkdir(self, path, mode=511, ignore_existing=False):
        ''' Augments mkdir by adding an option to not fail if the folder exists  '''
        try:
            self._sftp.mkdir(path, mode)
        except IOError:
            if ignore_existing:
                pass
            else:
                raise

    def fetch_files(self, remote_path, local_path):
        """
        :param remote_path: e.g. '/tmp/project/', '/tmp/debug.log'
        :param local_path: e.g. '/tmp/project/', '/tmp/debug.log'
        """
        _LOGGER.info('fetching files from {0} (remote) to {1} (local)'.format(remote_path, local_path))
        local_dir = os.path.dirname(local_path)
        assert os.path.exists(local_dir)

        if self._ssh_client:
            if stat.S_ISDIR(self._sftp.stat(remote_path).st_mode):
                self._ssh_fetch_folder(remote_path, os.path.join(local_dir, os.path.basename(remote_path)))
            else:
                self._sftp.get(remote_path, local_path)
        else:
            response, _ = self._docker_container.get_archive(remote_path)
            tar_xz(response.data, local_dir)

    def _ssh_fetch_folder(self, remote_path, local_path):
        if not os.path.exists(local_path):
            os.mkdir(local_path)

        for f in self._sftp.listdir(remote_path):
            if stat.S_ISDIR(self._sftp.stat(os.path.join(remote_path, f)).st_mode):
                self._ssh_fetch_folder(os.path.join(remote_path, f), os.path.join(local_path, f))
            else:
                self._sftp.get(os.path.join(remote_path, f), os.path.join(local_path, f))
