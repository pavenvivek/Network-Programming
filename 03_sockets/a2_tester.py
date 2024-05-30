"""Ensure this file is in the same directory as your netster program.

usage:
python3 a2_tester.py (tcp|udp)
python3 a2_tester.py (tcp|udp) hello
python3 a2_tester.py (tcp|udp) asdf
python3 a2_tester.py (tcp|udp) rand
python3 a2_tester.py (tcp|udp) hibye
python3 a2_tester.py (tcp|udp) exit
python3 a2_tester.py (tcp|udp) hiexit
python3 a2_tester.py (tcp|udp) parallel
python3 a2_tester.py (tcp|udp) byehiexit (client|server)

(Add --verbose to any of the above commands to print extra information.)"""
from multiprocessing.dummy import Pool
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
ARGS = {"tcp": "", "udp": "-u"}
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

def perr(code):
    """
    Check the return value from expect(). 0 means success.  Other possibilities
    are px.EOF and px.TIMEOUT.
    """
    if code == 0:
        return
    print("While trying to start program, got:", ["EOF", "TIMEOUT"][code-1])
    sys.exit(1)

def start_server(arg):
    """
    Start server in a separate shell, and expect that server to print the
    HELLO_SERVER message.
    """
    CMD = choose_cmd()
    server = px.spawn(f"{CMD} {ARGS[arg]}", timeout=TIMEOUT)
    perr(server.expect([HELLO_SERVER, px.EOF, px.TIMEOUT]))
    return server

def start_client(arg):
    """
    Start client in a separate shell, and expect that client to print the
    HELLO_CLIENT message.
    """
    CMD = choose_cmd()
    client = px.spawn(f"{CMD} {ARGS[arg]} localhost", timeout=TIMEOUT)
    perr(client.expect([HELLO_CLIENT, px.EOF, px.TIMEOUT]))
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
        print(c.before.decode())
        sys.exit(1)

def start_and_test(cli_type):
    """
    Wrapper function for spawning multiple anonymous clients in parallel.
    """
    CMD = choose_cmd()
    c = start_client(cli_type)
    def test_client_curry(m1, m2):
        return arrow(test_client(c, m1, m2))
    return test_client_curry

def arrow(msg):
    return f"{msg[0]} -> {msg[1]}"

def tbl(msgs):
    for m in msgs:
        print(arrow(m))

def err_words(words):
    print("Command must be one of the following:")
    for w in words:
        print('   ', w)

def show(f):
    def wrapper(*args, **kwargs):
        if args[0].__dict__['_verbose']:
            for m in f.__doc__.strip().split("\n"):
                print("   ", m.strip())
        return f(*args, **kwargs)
    return wrapper

class Test:
    """
    Handles setting up a server and one or more clients.
    Prints an explanation of each test if you set verbose=True.
    """
    def __init__(self, tcp_or_udp, command, prnt, verbose=False):
        self._verbose = verbose
        self._command = command
        self._prnt = prnt
        self._tu = tcp_or_udp
        self._s = start_server(self._tu)
        self._c = start_client(self._tu)

    @show
    def hello(self):
        """Send 'hello' from client to server, expect 'world' response."""
        print(arrow(test_client(self._c, "hello", "world")))

    @show
    def asdf(self):
        """Send 'asdf' from client to server, expect 'asdf' response."""
        print(arrow(test_client(self._c, "asdf", "asdf")))

    @show
    def hibye(self):
        """
        First send 'hello' to the server, expecting 'world' response, next send
        'goodbye', expecting 'farewell' response.
        """
        t = [test_client(self._c, "hello", "world")]
        t.append(test_client(self._c, "goodbye", "farewell"))
        tbl(t)

    @show
    def rand(self):
        """
        Choose a random word from a list, send it to the server, and expect
        the same word in response.
        """
        m = rand_message()
        msg, rsp = test_client(self._c, m, m)
        if msg == rsp:
            print("random word echo test passed")

    @show
    def byehiexit(self):
        """
        Send 'goodbye' from the initial client, expecting 'farewell' response.
        Next send 'hello' from a second client, expecting 'world' response.
        Finally send 'exit' from the second client, expecting 'ok' response.
        The next argument (either 'client' or 'server') specifies what the test
        should print.  For 'client', print the client-side interaction, for
        'server', print the server-side logs. The logs won't show the actual
        port number, but instead each distinct connection, e.g: <port_1>.
        """
        cli_srv = ["client", "server"]
        if self._prnt not in cli_srv:
            print(f"When testing 'byehiexit' command, also specify one of {cli_srv}")
            sys.exit(1)

        t = [test_client(self._c, "goodbye", "farewell")] # stop the first client
        c = start_client(tu) # start the second client
        t.append(test_client(c, "hi", "hi"))
        t.append(test_client(c, "exit", "ok"))
        if self._prnt == "client":
            tbl(t)

        if self._prnt == "server":
            response = self._s.before + self._s.after
            self._s.expect(".*\r\n")
            response += self._s.before + self._s.after
            self._s.expect(px.EOF)
            print ("self._s -> {}".format(self._s))
            logs = self._s.before.decode().replace("...\r\n", "")
            print ("logs -> {}".format(logs))
            ports = sorted({
                re.search(R"[^,]*, ([0-9]+)", st, re.M).group(1)
                for st in filter(None, logs.split('\n'))
            })
            for port in ports:
                logs = logs.replace(port, f"<port_{ports.index(port)}>")

            logs = '\n'.join(sorted(set(logs.split("\n"))))
            print(response.decode().replace("...\r", "") + logs)

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
            ["goodbye", "farewell"],
        ]
        with Pool(4) as p:
            results = [p.apply_async(start_and_test(self._tu), m) for m in msgs]
            for r in results:
                print(r.get(timeout=1))

    @show
    def hiexit(self):
        """
        Send 'hello', expecting 'world', then send 'exit', expecting 'ok'. First print
        the formatted client-side output, and then print the server-side output.
        """
        t = [test_client(self._c, "hi", "hi")]
        t.append(test_client(self._c, "exit", "ok"))
        tbl(t)
        sout = self._s.before + self._s.after
        self._s.expect(px.EOF)
        print((sout + self._s.before).decode().replace("...\r\n", "\n"))

    @show
    def exit(self):
        """
        Send 'goodbye', expecting 'ok'. First print the formatted client-side
        output, then print the server-side output.
        """
        print(arrow(test_client(self._c, "exit", "ok")))
        sout = self._s.before + self._s.after
        self._s.expect(px.EOF)
        print((sout + self._s.before).decode().replace("...\r\n", "\n"))


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv.remove("--verbose")

    assert len(sys.argv[1:]), "Expected more args. Use -h for help."
    if sys.argv[1] not in ["tcp", "udp"]:
        print("First arg must be either 'tcp' or 'udp'")
        sys.exit(0)

    tu = sys.argv[1]
    word = sys.argv[2] if len(sys.argv[2:]) else None
    prnt = sys.argv[3] if len(sys.argv[3:]) else None
    if word == None:
        s = start_server(tu)
        print((s.before+s.after).decode())
        sys.exit(0)

    tst = Test(tu, word, prnt, verbose)
    words = [x for x in dir(tst) if not x.startswith("_")]
    if not hasattr(tst, str(word)):
        print(f"Unrecognized command ({word}).")
        err_words(words)
        sys.exit(1)

    getattr(tst, word)()
