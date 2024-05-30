#!/usr/bin/env python3
import argparse
import sys

# Import the assignment modules.
#try:
#    from a2 import *
#except ImportError:
#    print("import of module a2 failed", file=sys.stderr)
try:
    from a3 import *
except ImportError:
    print("import of module a3 failed", file=sys.stderr)
#try:
#    from a4 import *
#except ImportError:
#    print("import of module a4 failed", file=sys.stderr)


DEFAULT_PORT=8200 #12345

# If we are a server, launch the appropriate methods to handle server
# functionality based on the input arguments.
# NOTE: The arguments should be extended with a custom dict or **kwargs
def run_server(host, port, **kwargs):

    if isinstance(port, str):
        port = int(port)

    print("Hello, I am a server")
    server = Server(host, port, kwargs["file_handle"])

    if kwargs["protocol_udp"]:
        print ("udp server")
        server.run_udp_server()
    elif kwargs["protocol_rudp"] == 0:
        print ("udp file server")
        server.run_udp_server_file()    
    elif kwargs["protocol_rudp"] == 1:
        print ("rudp server")
        server.run_rudp_server()
    elif kwargs["protocol_rudp"] == 2:
        print ("go-back-N server")
        server.run_gbn_server()
    else:
        print ("tcp server")
        server.run_tcp_server()

# If we are a client, launch the appropriate methods to handle client
# functionality based on the input arguments
# NOTE: The arguments should be extended with a custom dict or **kwargs
def run_client(host, port, **kwargs):

    if isinstance(port, str):
        port = int(port)

    print("Hello, I am a client")
    client = Client(host, port, kwargs["file_handle"])

    if kwargs["protocol_udp"]:
        print ("udp client")
        client.run_udp_client()
    elif kwargs["protocol_rudp"] == 0:
        print ("udp file client")
        client.run_udp_client_file()    
    elif kwargs["protocol_rudp"] == 1:
        print ("rudp client")
        client.run_rudp_client()
    elif kwargs["protocol_rudp"] == 2:
        print ("go-back-N client")
        client.run_gbn_client()
    else:
        print ("tcp client")
        client.run_tcp_client()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SICE Network netster")
    parser.add_argument("-p", "--port", type=str, default=DEFAULT_PORT,
                        help="listen on/connect to PORT (default={}"
                        .format(DEFAULT_PORT))
    parser.add_argument("-i", "--iface", default="0.0.0.0",
                        help="listen on interface IFACE")
    parser.add_argument("-f", "--file",
                        help="file to read/write")
    parser.add_argument("-u", "--udp", action="store_true",
                        help="use UDP (default TCP)")
    parser.add_argument("-r", "--rudp", type=int, default=0,
                        help="use RUDP (1=stopwait, 2=gobackN)")
    parser.add_argument("host", metavar="host", type=str, nargs="?",
                        help="connect to server at HOST")

    args = parser.parse_args()

    f = None
    # open the file if specified
    if args.file:
        try:
            # client should read the file,
            # server should write the file
            mode = "r" if args.host else "w"
            f = open(args.file, mode)
        except Exception as e:
            print("Could not open file: {}".format(e))
            exit(1)

    # Here we determine if we are a client or a server depending
    # on the presence of a "host" argument.
    if args.host:
        run_client(args.host, args.port, protocol_udp=args.udp, protocol_rudp=args.rudp, file_handle=f)
    else:
        run_server(args.host, args.port, protocol_udp=args.udp, protocol_rudp=args.rudp, file_handle=f)

    if args.file:
        f.close()
