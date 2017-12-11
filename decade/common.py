#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Curtis Yu
@contact: cuyu@splunk.com
@since: 06/12/2017
"""
import socket
import tarfile
import os

try:
    from cStringIO import StringIO as BIO
except ImportError:  # python 3
    from io import BytesIO as BIO


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def get_unoccupied_port():
    s = socket.socket()
    s.bind(('', 0))

    return s.getsockname()[1]


def check_if_bind(s, ip, port):
    ret = s.connect_ex((ip, int(port)))
    print ret
    if not ret:
        return True
    else:
        return False


def tar_cz(*path):
    """tar_cz(*path) -> bytes
    Compress a sequence of files or directories in memory.
    The resulting string could be stored as a .tgz file."""
    file_out = BIO()
    tar = tarfile.open(mode="w:gz", fileobj=file_out)
    for p in path:
        tar.add(p, arcname=os.path.basename(p))
    tar.close()
    return file_out.getvalue()


def tar_xz(stringz, folder="."):
    """tar_xz(stringz, folder = ".") -> None
    Uncompress a string created by tar_cz in a given directory."""
    file_in = BIO(stringz)
    tar = tarfile.open(mode="r", fileobj=file_in)
    tar.extractall(folder)
