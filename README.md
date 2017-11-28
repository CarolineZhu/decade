# decade

> An automatic remote debug configurator for Pycharm.


Pycharm provides remote debug function but needs complex configuration process.
Decade makes this process fully automatic.This project was started and maintained by Ruiyuan Zhu (rzhu@splunk.com)


### Getting started

To start a decade:
```
decade --remote-path=<remote_path> --src-entry=<src_code> --server-name=<server_name> --hostname=<hostname> --ssh-user=<ssh_user> --ssh-password=<ssh_password> --ssh-port=<ssh_port> --local-path=<local_path> --local-ip=<local_ip> --local-port=<local_port>
```

- `<remote_path>`: project path on remote client
- `<src_code>`: the entry python file of source code
- `<server_name>`(optional, default hello): debug server name defined arbitrarily by user
- `<hostname>`: remote client hostname
- `<ssh_user>`: remote client ssh user
- `<ssh_password>`: remote client ssh password
- `<ssh_port>`(optional, default 22): remote client ssh port
- `<download>`(optional, store true): add if want to download the whole project to local. 
- `<local_path>`: project path on local server(Create an empty folder to contain the remote project if downloading the whole project, or use the local project path)
- `<local_ip>`: local server ip address
- `<local_port>`: local server remote debug port(Any unoccupied port is ok)

For example,
```
decade --remote-path=/root/hello --src-entry=hello.py --server-name=hello --hostname=systest-sca-linux05 --ssh-user=root --ssh-password=sp1unk --ssh-port=22 --local-path=/Users/rzhu/pytest_practice/try6 --local-ip=10.66.4.54 --local-port=52001
```


### Configuring process finished

When this message shows in terminal, 
```
The configuring process finished successfully. Open the project and start the debug server. Enter r if debug server started:
```
Open the project with Pycharm. Click the debug button in the Pycharm to start the debug server. Enter 'r' if ready.

Then the debugger will stop at the next line of 
```
pydevd.settrace(args.local_ip, port=args.local_port, stdoutToServer=True, stderrToServer=True)
```

You can set breakpoints in your project as your wish.

Go for debugging!

