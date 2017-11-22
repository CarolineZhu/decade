import pydevd
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote-path",
                        help="project path on remote client")
    parser.add_argument("--src-entry",
                        help="the entry python file of source code")
    parser.add_argument("--local-ip",
                        help="local server ip address")
    parser.add_argument("--local-port", type=int,
                        help="local server remote debug port, any unoccupied port is ok")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    pydevd.settrace(args.local_ip, port=args.local_port, stdoutToServer=True, stderrToServer=True)
    src_code = args.remote_path + '/' + args.src_entry
    execfile(src_code)