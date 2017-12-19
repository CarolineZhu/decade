import os
from shutil import copyfile

_SOURCE = '/tmp/decade_resource/sitecustomize.py'


def prepare(path, lib_name):
    lib_path = path.replace('bin', lib_name)
    if not os.path.exists(lib_path):
        return

    for d in os.listdir(lib_path):
        if d.startswith('python') and os.path.exists(os.path.join(lib_path, d, 'site.py')):
            if not os.path.exists(os.path.join(lib_path, d, 'sitecustomize.py')):
                print 'Copy sitecustomize.py to {0}'.format(os.path.join(lib_path, d))
                copyfile(_SOURCE, os.path.join(lib_path, d, 'sitecustomize.py'))


if __name__ == "__main__":
    for path in os.environ['PATH'].split(':'):
        prepare(path, 'lib')
        prepare(path, 'lib64')
