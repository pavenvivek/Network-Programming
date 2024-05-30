"""The autograder uses this program to test your netster/a2 code

You can also use it yourself, for example (on silo):

pip3 install --user pexpect # first time
cd Net-Fall20/src/py  # if you are testing netster.py
python3 ../a2_tester.py --port 1234 --udp byehiexit --server
"""
f"If you see this message, use Python3.6 or greater."
from multiprocessing.dummy import Pool
import argparse
import os
import random
import re
import sys
import time

try:
    import pexpect as px
except:
    print("Install pexpect: pip3 install --user pexpect")
    sys.exit(1)


# CONSTANTS
TIMEOUT = 1
HELLO_SERVER = "Hello, I am a server"
HELLO_CLIENT = "Hello, I am a client"

def choose_cmd():
    """
    Change the name of CMD depending on if students upload python3 or C
    solution. For testing the C version, you have to run "make" before this
    tester, to create the "netster" binary.
    """
    if "netster.c" in os.listdir():
        return "./netster"
    elif "netster.py" in os.listdir():
        version = sys.version_info
        assert version >= (3,6), "Requires python version >= 3.6"
        version_string = '.'.join(map(str, version[:2]))
        return f"python{version_string} netster.py"
    else:
        print("This tester must be present (or linked) in the same directory as",
            "a netster.c or netster.py file.")
        sys.exit(1)

def perr(progtype, prog, expectations):
    """
    Check the return value from expect(). 0 means success. Other possibilities
    are px.EOF and px.TIMEOUT.
    """
    code = prog.expect(expectations)
    if code == 0:
        return
    print(f"While trying to start {progtype}, got {['EOF', 'TIMEOUT'][code-1]}")
    print("(expected)\t", HELLO_CLIENT if progtype == 'client' else HELLO_SERVER)
    print(f"(your {progtype})\t", prog.before)
    sys.exit(1)

def start_server(args, logfile):
    """
    Start server in a separate shell, and expect that server to print the
    HELLO_SERVER message.
    """
    CMD = choose_cmd()
    server = px.spawn(f"{CMD} {args}", timeout=TIMEOUT, encoding='utf-8')
    perr('server', server, [HELLO_SERVER, px.EOF, px.TIMEOUT])
    server.logfile = logfile
    return server

def start_client(args):
    """
    Start client in a separate shell, and expect that client to print the
    HELLO_CLIENT message.
    """
    CMD = choose_cmd()
    client = px.spawn(f"{CMD} {args} localhost", timeout=TIMEOUT, encoding='utf-8')
    perr('client', client, [HELLO_CLIENT, px.EOF, px.TIMEOUT])
    return client

def rand_message():
    """Return random message from hard-coded list."""
    rand_msgs = ["asdf", "hjkl", "qwerty"]
    return rand_msgs[random.randint(0, len(rand_msgs)-1)]

def test_client(c, msg, rsp):
    """
    Given an already-started client c, send it a message and expect
    a response. If the client returns EOF or times out, error and exit.
    """
    try:
        time.sleep(min(random.random(), 0.5))
        c.expect("\r\n*")
        c.sendline(msg)
        c.expect(rsp)
        return [msg, rsp]
    except (px.EOF, px.TIMEOUT):
        print(f"   Client expected '{rsp}' but got something else:", "\n")
        print(c.before)
        sys.exit(1)

def start_and_test(client_args):
    """
    Wrapper function for spawning multiple anonymous clients in parallel.
    """
    CMD = choose_cmd()
    c = start_client(client_args)
    def test_client_curry(m1, m2):
        return arrow(test_client(c, m1, m2))
    return test_client_curry

def arrow(msg):
    return f"{msg[0]} -> {msg[1]}"

def tbl(msgs):
    for m in msgs:
        print(arrow(m))

def show(f):
    def wrapper(*args, **kwargs):
        if args[0].__dict__['verbose']:
            for m in f.__doc__.strip().split("\n"):
                print("   ", m.strip())
        return f(*args, **kwargs)
    return wrapper

class Test:
    """
    Handles setting up a server and one or more clients.
    Prints an explanation of each test if you set verbose=True.
    """
    def __init__(self, args, print_server, srv_log, verbose=False):
        self.verbose = verbose
        self.print_server = print_server
        self.netster_args = args
        self.server = start_server(self.netster_args, srv_log)
        #self.server.logfile_read = sys.stdout
        self.client = start_client(self.netster_args)

    @show
    def hello(self):
        """Send 'hello' from client to server, expect 'world' response."""
        print(arrow(test_client(self.client, "hello", "world")))

    @show
    def asdf(self):
        """Send 'asdf' from client to server, expect 'asdf' response."""
        print(arrow(test_client(self.client, "asdf", "asdf")))

    @show
    def hibye(self):
        """
        First send 'hello' to the server, expecting 'world' response, next send
        'goodbye', expecting 'farewell' response.
        """
        t = [test_client(self.client, "hello", "world")]
        t.append(test_client(self.client, "goodbye", "farewell"))
        tbl(t)

    @show
    def rand(self):
        """
        Choose a random word from a list, send it to the server, and expect
        the same word in response.
        """
        m = rand_message()
        msg, rsp = test_client(self.client, m, m)
        if msg == rsp:
            print("random word echo test passed")

    @show
    def byehiexit(self):
        """
        Send 'goodbye' from the initial client, expecting 'farewell' response.
        Next send 'hello' from a second client, expecting 'world' response.
        Finally send 'exit' from the second client, expecting 'ok' response.
        The next argument (either 'client' or 'server') specifies what the test
        should print.

        For 'client', print the client-side interaction only.

        For 'server', print the server-side logs. Instead of the actual port
        number, use an incrementing ID like port_1, port_2, etc.

        The port number is expected to appear after a comma, such as:

        got message from ('127.0.0.1', 58253)
        server log 127.0.0.1, 58253

        The expected token sequence is: <COMMA> <SPACE> <PORT_NUMBER>
        """
        t = [test_client(self.client, "goodbye", "farewell")] # stop the first client
        c = start_client(self.netster_args) # start the second client
        t.append(test_client(c, "hi", "hi"))
        t.append(test_client(c, "exit", "ok"))
        if self.print_server:
            response = self.server.before + self.server.after
            self.server.expect(".*\r\n")
            response += self.server.before + self.server.after
            self.server.expect(px.EOF)
            logs = self.server.before.replace("...\r\n", "")
            ports = set()
            for st in filter(None, logs.split('\n')):
                try:
                    match = re.search("([0-9]{4,})", st, re.M)
                    ports.add(int(match.group(1)))
                except AttributeError:
                    print("Could not find port number (4+ digits) in server output:", file=sys.stderr)
                    print(st, file=sys.stderr)
                    sys.exit(1)
            ports = sorted(ports) # convert to sorted list, so we can .index into it
            for port in ports:
                logs = logs.replace(str(port), f"<port_{ports.index(port)}>")

            logs = '\n'.join(sorted(set(logs.split("\n"))))
            print(response.replace("...\r", "") + logs)
        else:
            tbl(t)

    @show
    def parallel(self):
        """
        Test multiple clients sending in parallel. The clients are spawned
        asynchronously but their results are gathered and printed in their
        original order, once all the clients finish sending.
        """
        msgs = [
            ["hello", "world"],
            # Uncomment next line to test non-determinism.
            # If the following line is tested last, then everything will print.
            # Otherwise, the test will raise an error.
            #["exit", "ok"],
            ["a", "a"],
            ["b", "b"],
            ["c", "c"],
            # ["d", "d"],
            # ["e", "e"],
            # ["f", "f"],
            ["goodbye", "farewell"],
        ]
        with Pool(4) as p:
            results = [p.apply_async(start_and_test(self.netster_args), m) for m in msgs]
            for r in results:
                print(r.get(timeout=2))

    @show
    def hiexit(self):
        """
        Send 'hello', expecting 'world', then send 'exit', expecting 'ok'. First print
        the formatted client-side output, and then print the server-side output.
        """
        t = [test_client(self.client, "hi", "hi")]
        t.append(test_client(self.client, "exit", "ok"))
        tbl(t)
        sout = self.server.before + self.server.after
        self.server.expect(px.EOF)
        print((sout + self.server.before).replace("...\r\n", "\n"))

    @show
    def exit(self):
        """
        Send 'goodbye', expecting 'ok'. First print the formatted client-side
        output, then print the server-side output.
        """
        print(arrow(test_client(self.client, "exit", "ok")))
        sout = self.server.before + self.server.after
        self.server.expect(px.EOF)
        print((sout + self.server.before).replace("...\r\n", "\n"))


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-u", "--udp", action="store_true", help="use UDP (default: TCP)")
    p.add_argument("-v", "--verbose", action="store_true", help="print verbose info")
    p.add_argument("--port", help="specify non-default port (>1024)")
    s = p.add_subparsers(dest="command")
    c_hello = s.add_parser("hello", help="Send 'hello' from client, expecting 'world' response")
    c_asdf = s.add_parser("asdf", help="Send 'asdf' from client, expecting 'asdf' response")
    c_rand = s.add_parser("rand", help="Send a random word from a list, expect same word in response")
    c_hibye = s.add_parser("hibye", help="Send 'hello' then 'goodbye'")
    c_exit = s.add_parser("exit", help="Send 'exit', which should stop the server")
    c_hiexit = s.add_parser("hiexit", help="Send 'hello', followed by 'exit'")
    c_parallel = s.add_parser("parallel", help="Start multiple clients at the same time")
    c_byehiexit = s.add_parser("byehiexit", help="Send 'goodbye', then say 'hello' then 'exit' from another client")
    c_byehiexit.add_argument("--server", action='store_true', help="Display server output (default: client)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    netster_args = "-u" if args.udp else ""
    netster_args += (" -p " + args.port) if args.port else ""
    log1 = open("server.log", "w+")
    if not args.command:
        s = start_server(netster_args, log1)
        print(s.before+s.after)
        sys.exit(0)

    tst = Test(netster_args, args.server if 'server' in args else None, log1, args.verbose)
    try:
        getattr(tst, args.command)()
    finally:
        # get rest of server output
        tst.server.expect([px.TIMEOUT, px.EOF])
        log1.close()
        with open("server.log") as f:
            lines = f.readlines()
            for ln in lines:
                print(ln, end="", file=sys.stderr)
