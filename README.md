# decade

> An automatic remote debug configurator for Pycharm (on mac OS).


Pycharm provides remote debug function but needs complex configuration process.
Decade makes this process fully automatic.This project was started and maintained by Ruiyuan Zhu (rzhu@splunk.com)


### Getting started

To install decade:
```
pip install decade
```

To start a decade:
```
decade --remote-path=<remote_path> --src-entry=<src_code> --server-name=<server_name> --hostname=<hostname> --ssh-user=<ssh_user> --ssh-password=<ssh_password> --ssh-port=<ssh_port> --local-path=<local_path> --download
```

- `<remote_path>`: project path on remote client
- `<src_code>`: the entry python file of source code
- `<server_name>`(optional, default hello): debug server name defined arbitrarily by user
- `<hostname>`: remote client hostname
- `<ssh_user>`: remote client ssh user
- `<ssh_password>`: remote client ssh password
- `<ssh_port>`(optional, default 22): remote client ssh port
- `--download`(optional, store true): add if want to download the whole project to local. 
- `<local_path>`: project path on local server(Create an empty folder to contain the remote project if downloading the whole project, or use the local project path)

For example,
```
decade --remote-path=/root/hello --src-entry=hello.py --server-name=hello --hostname=systest-sca-linux05 --ssh-user=root --ssh-password=sp1unk --local-path=/Users/rzhu/pytest_practice/try6
```

Also support remote debug code in docker container (just leave `--ssh-user` and `--ssh-password` empty and set `--hostname` to the container id):

```
decade --remote-path=/root/hello --src-entry=hello.py --server-name=hello --hostname=b294bc47bdc0 --local-path=/Users/rzhu/pytest_practice/try6
```

### Configuring process finished

When this message shows in terminal
```
Configuration done. Please start the debug server in PyCharm.
```
and local project is opened by Pycharm, 

Click the debug button in the Pycharm to start the debug server. Enter 'r'/'ready' if ready.

Then the debugger will stop at the next line of 
```
pydevd.settrace(args.local_ip, port=args.local_port, stdoutToServer=True, stderrToServer=True)
```

You can set breakpoints in your project as your wish.

Go for debugging!


### Todo

- Use env variables to store the local project path (so that we can store config in a shell script, a optional way to use the cmd easier)
    - Give the content of the shell script, like the `~/.orca/env.sh`
    - In the end of the shell script, call `source ./env.sh`, so that user just need to call one script when debugging on apps jenkins
- ~~Use `open -a PyCharm <project_path>` to open the PyCharm after script running~~
- ~~Support remote debugging in docker containers~~
- Add unit test
- ~~Use os.path.join instead of `+`~~
- Use git to make sure the local code is the latest version (if local-path is exist)
- Remove --download option, and download the code automatically if the local-path is not exist
- ~~Remove the query for if the debug server is ready (maybe can use a loop to see if the PyCharm process's binding port is right)~~