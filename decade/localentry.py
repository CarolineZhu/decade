import os, sys
import stat
import subprocess
import paramiko
import xml.etree.ElementTree as et
import argparse
import pkgutil
import shutil
from common import get_host_ip, get_unoccupied_port
from client import Client


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote-path",
                        help="project path on remote client")
    parser.add_argument("--src-entry",
                        help="the entry python file of source code")
    parser.add_argument("--server-name", default='hello',
                        help="ide webserver name")
    parser.add_argument("--hostname",
                        help="remote client hostname")
    parser.add_argument("--ssh-user",
                        help="remote client ssh user")
    parser.add_argument("--ssh-password",
                        help="remote client ssh password")
    parser.add_argument("--ssh-port",
                        help="remote client ssh port", type=int, default=22)
    parser.add_argument("--local-path",
                        help="project path on local server")
    parser.add_argument("--download",
                        help="download the whole source code of the project",
                        action='store_true',
                        default=False)
    arguments = parser.parse_args()
    return arguments


# setup virtualenv
def virtualenv_setup(remote_path, client, local_project_path):
    new_cmd = 'virtualenv venv'
    client.execute(new_cmd)

    activate_cmd = 'source ./venv/bin/activate'
    client.execute(activate_cmd)

    requirements_path = os.path.join(remote_path, 'requirements.txt')
    if os.path.exists(os.path.join(local_project_path, remote_path, 'requirements.txt')):
        config_cmd = 'pip install -r ' + requirements_path
        client.execute(config_cmd)


def edit_config_files(f, file_location, local_path, args_list):
    init_config = et.parse(file_location)
    root = init_config.getroot()
    for item in args_list:
        for ele in root.iter(item['tag']):
            for attrib_key in item['attrib'].keys():
                ele.set(attrib_key, item['attrib'][attrib_key])
    init_config.write(os.path.join(local_path, '.idea/', f))


def IDE_config(args, remote_path, project_name, local_path, local_ip, local_port, ssh_port):
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
                                mapping.set('local-root', '$PROJECT_DIR$' + remote_path)
                                mapping.set('remote-root', remote_path)
    workspace_config.write(os.path.join(local_path, 'idea', 'workspace.xml'))

    # iml
    shutil.copyfile(os.path.join(pycharm_config_dir, 'try.iml'),
                    os.path.join(local_path, '.idea', project_name + '.iml'))


def main():
    args = parse_args()
    remote_path = args.remote_path
    serverName = args.server_name

    hostname = args.hostname
    ssh_user = args.ssh_user
    ssh_password = args.ssh_password
    ssh_port = args.ssh_port

    python_package = os.path.join(remote_path, 'venv/bin/python')
    local_project_path = args.local_path
    local_ip = get_host_ip()
    local_port = get_unoccupied_port()
    project_name = os.path.split(local_project_path)[-1]
    url = ssh_user + '@' + hostname + ':' + str(ssh_port)

    ideConfig = {
        "deployment": [
            {'tag': 'component', 'attrib': {'serverName': serverName}},
            {'tag': 'paths', 'attrib': {'name': serverName}},
            {'tag': 'mapping', 'attrib': {'deploy': remote_path, 'local': '$PROJECT_DIR$' + remote_path}}
        ],
        "misc": [
            {'tag': 'component', 'attrib': {'project-jdk-name':
                                                'Remote Python 2.7.5 (ssh://' + url + python_package + ')'}},
        ],
        "remote-mappings": [
            {'tag': 'remote-mappings', 'attrib': {'server-id': "python@ssh://" + url + python_package}},
            {'tag': 'mapping', 'attrib': {'local-root': '$PROJECT_DIR$' + remote_path, 'remote-root': remote_path}},
        ],
        "webServers": [
            {'tag': 'webServer', 'attrib': {'name': serverName, 'url': 'http://' + ssh_user + '@' + hostname}},
            {'tag': 'fileTransfer',
             'attrib': {'host': ssh_user + '@' + hostname, 'port': str(ssh_port), 'accessType': 'SFTP'}}
        ],
    }
    IDE_config(ideConfig, remote_path, project_name, local_project_path, local_ip, local_port, ssh_port)

    client = Client(args.hostname, args.ssh_user, args.ssh_password, args.ssh_port)

    client.send_files(os.path.join(pkgutil.get_loader("decade").filename, 'remoteentry.py'),
                      os.path.join(remote_path, 'remoteentry.py'))

    if args.download:
        local_ide_mkdir_cmd = ['mkdir', '-p', local_project_path + remote_path]
        subprocess.call(local_ide_mkdir_cmd)
        client.fetch_files(remote_path, local_project_path)

    elif not os.path.exists(os.path.join(local_project_path, remote_path, 'remoteentry.py')):
        client.fetch_files(os.path.join(remote_path, 'remoteentry.py'),
                           os.path.join(local_project_path, remote_path, 'remoteentry.py'))

    virtualenv_setup(remote_path, client, local_project_path)

    msg = raw_input(
        "The configuring process finished successfully. Open the project and start the debug server. Enter r if debug server started:")
    assert msg == 'r'

    run_remote_cmd = 'python {remote_entry} --remote-path {remote_path} --src-entry {src_entry} --local-ip {ip} --local-port {port}'.format(
        **{
            'remote_entry': os.path.join(remote_path, 'remoteentry.py'),
            'remote_path': remote_path,
            'src_entry': args.src_entry,
            'ip': local_ip,
            'port': local_port,
        })
    client.execute(run_remote_cmd)


if __name__ == "__main__":
    main()
