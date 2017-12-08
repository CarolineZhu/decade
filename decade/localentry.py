import os
import xml.etree.ElementTree as et
import argparse
import pkgutil
import shutil
from subprocess import call
from common import get_host_ip, get_unoccupied_port
from client import Client
import re
from colorama import init, Fore, Back, Style

init()

_REMOTE_ENTRY = 'remoteentry.py'
_VIRTUAL_ENV_NAME = 'virtual_decade'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote-path",
                        help="project path on remote client")
    parser.add_argument("--src-entry",
                        help="the entry python file of source code")
    parser.add_argument("--server-name", default='hello',
                        help="ide webserver name")
    parser.add_argument("--hostname",
                        help="remote client hostname or docker container id")
    parser.add_argument("--ssh-user",
                        help="remote client ssh user, do not set if is docker container")
    parser.add_argument("--ssh-password",
                        help="remote client ssh password, do not set if is docker container")
    parser.add_argument("--ssh-port",
                        help="remote client ssh port", type=int, default=22)
    parser.add_argument("--local-path",
                        help="project path on local server, will download from remote if not exist")
    parser.add_argument("--download",
                        help="download the whole source code of the project",
                        action='store_true',
                        default=False)
    arguments = parser.parse_args()
    return arguments


# setup virtualenv
def setup_virtualenv(client, local_project_path, src_entry, remote_path):
    new_cmd = 'virtualenv {0}'.format(_VIRTUAL_ENV_NAME)
    client.execute(new_cmd)

    activate_cmd = 'source ./{0}/bin/activate'.format(_VIRTUAL_ENV_NAME)
    client.execute(activate_cmd)

    def _find_requirements_until_root(root_dir, sub_dir):
        assert root_dir in sub_dir

        if os.path.exists(os.path.join(sub_dir, 'requirements.txt')):
            return os.path.join(sub_dir.replace(root_dir, ''), 'requirements.txt')
        else:
            return _find_requirements_until_root(root_dir, os.path.dirname(sub_dir))

    # Install pydevd in remote
    client.execute('pip install pydevd')

    # Check the direct folder of the src entry file first, if no requirements.txt, then check the upper folder...
    src_path = os.path.join(local_project_path, *re.split(r'[/\\]*', src_entry))
    if os.path.exists(os.path.join(local_project_path, 'requirements.txt')):
        config_cmd = 'pip install -r {0}'.format(
            os.path.join(remote_path, _find_requirements_until_root(local_project_path, src_path)))
        client.execute(config_cmd)


def edit_config_files(f, file_location, local_path, args_list):
    init_config = et.parse(file_location)
    root = init_config.getroot()
    for item in args_list:
        for ele in root.iter(item['tag']):
            for attrib_key in item['attrib'].keys():
                ele.set(attrib_key, item['attrib'][attrib_key])
    init_config.write(os.path.join(local_path, '.idea', f))


def config_IDE(args, remote_path, project_name, local_path, local_ip, local_port, ssh_port):
    local_idea_path = os.path.join(local_path, '.idea')
    if not os.path.exists(local_idea_path):
        os.mkdir(local_idea_path)
    else:
        shutil.rmtree(local_idea_path)
        os.mkdir(local_idea_path)

    script_path = pkgutil.get_loader("decade").filename
    print script_path

    # other config files
    pycharm_config_dir = os.path.join(script_path, 'pycharm_config')
    raw_files = os.listdir(pycharm_config_dir)
    for f in raw_files:
        file_location = os.path.join(pycharm_config_dir, f)
        file_name = os.path.splitext(f)[0]
        if file_name == 'workspace' or file_name == 'webServer' or file_name == 'try':
            continue
        config_list = args[file_name]
        edit_config_files(f, file_location, local_path, config_list)

    # webServers.xml
    webservers_config = et.parse(os.path.join(pycharm_config_dir, 'webServers.xml'))
    webservers_root = webservers_config.getroot()
    for ele in webservers_root.iter('option'):
        if 'name' in ele.attrib.keys() and ele.get('name') == "port":
            ele.attrib['value'] = str(ssh_port)
    webservers_config.write(os.path.join(pycharm_config_dir, 'webServers.xml'))
    edit_config_files('webServers.xml', os.path.join(pycharm_config_dir, 'webServers.xml'), local_path,
                      args['webServers'])

    # workspace.xml
    workspace_config = et.parse(os.path.join(pycharm_config_dir, 'workspace.xml'))
    workspace_root = workspace_config.getroot()
    for ele in workspace_root.iter('option'):
        if 'name' in ele.attrib.keys() and ele.get('name') == "myItemId":
            ele.attrib['value'] = project_name
    for ele in workspace_root.iter('component'):
        if 'name' in ele.attrib.keys() and ele.get('name') == "RunManager":
            ele.attrib['selected'] = 'Python Remote Debug.debug1'
            debugger_list = ele.findall('configuration')
            for debugger in debugger_list:
                if 'type' in debugger.attrib.keys() and debugger.get('type') == "PyRemoteDebugConfigurationType":
                    debugger.set('name', 'debug1')
                    for option in debugger.iter('option'):
                        if 'name' in option.attrib.keys() and option.get('name') == 'PORT':
                            option.set('value', str(local_port))
                        if 'name' in option.attrib.keys() and option.get('name') == 'HOST':
                            option.set('value', local_ip)
                        if 'name' in option.attrib.keys() and option.get('name') == 'pathMappings':
                            # mappings = option.iter('mapping')
                            for mapping in option.iter('mapping'):
                                mapping.set('local-root', '$PROJECT_DIR$')
                                mapping.set('remote-root', remote_path)
    workspace_config.write(os.path.join(local_path, '.idea', 'workspace.xml'))

    # iml
    shutil.copyfile(os.path.join(pycharm_config_dir, 'try.iml'),
                    os.path.join(local_path, '.idea', project_name + '.iml'))


def main():
    args = parse_args()
    remote_path = args.remote_path or os.environ.get('DECADE_REMOTE_PATH')
    assert remote_path
    server_name = args.server_name
    ssh_port = args.ssh_port
    local_project_path = args.local_path or os.environ.get('DECADE_LOCAL_PATH')
    assert local_project_path
    local_ip = get_host_ip()
    local_port = get_unoccupied_port()
    project_name = os.path.split(remote_path)[-1]

    ide_config = {
        "deployment": [
            {'tag': 'component', 'attrib': {'serverName': server_name}},
            {'tag': 'paths', 'attrib': {'name': server_name}},
            {'tag': 'mapping', 'attrib': {'deploy': remote_path, 'local': '$PROJECT_DIR$' + remote_path}}
        ],
        "misc": [
        ],
        "remote-mappings": [
            {'tag': 'mapping', 'attrib': {'local-root': '$PROJECT_DIR$' + remote_path, 'remote-root': remote_path}},
        ],
        "webServers": [
        ],
    }

    client = Client(args.hostname, args.ssh_user, args.ssh_password, args.ssh_port)

    client.send_files(os.path.join(pkgutil.get_loader("decade").filename, _REMOTE_ENTRY),
                      os.path.join(remote_path, _REMOTE_ENTRY))

    if args.download:
        client.fetch_files(remote_path, local_project_path)
        # If need to download the source code from remote, the project path need to append the project name
        local_project_path = os.path.join(local_project_path, os.path.basename(remote_path))
    elif not os.path.exists(os.path.join(local_project_path, _REMOTE_ENTRY)):
        local_project_path = os.path.join(local_project_path, os.path.basename(remote_path))
        client.fetch_files(os.path.join(remote_path, _REMOTE_ENTRY),
                           os.path.join(local_project_path, _REMOTE_ENTRY))

    config_IDE(ide_config, remote_path, project_name, local_project_path, local_ip, local_port, ssh_port)

    setup_virtualenv(client, local_project_path, args.src_entry, remote_path)

    call(['open', '-a', 'PyCharm', local_project_path])

    msg = raw_input(
        "Configuration done. Please start the debug server in PyCharm.\nEnter {0}/{1} if debug server started:".format(
            Fore.RED + 'r' + Style.RESET_ALL, Fore.RED + 'ready' + Style.RESET_ALL))
    assert msg in ['r', 'ready']

    run_remote_cmd = 'python {remote_entry} --remote-path {remote_path} --src-entry {src_entry} --local-ip {ip} --local-port {port}'.format(
        **{
            'remote_entry': os.path.join(remote_path, _REMOTE_ENTRY),
            'remote_path': remote_path,
            'src_entry': args.src_entry,
            'ip': local_ip,
            'port': local_port,
        })
    client.execute(run_remote_cmd)


if __name__ == "__main__":
    main()
