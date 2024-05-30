##################################################
# File name:    a2.py                            #  
# Desceription: Socket Assignment                #
# Author:       Paventhan Vivekanandan           #
# mail-id:      pvivekan@iu.edu                  #
# Course:       Computer Networks [P538]         #
##################################################

#!/usr/bin/env python3

import sys
import socket
import threading
import queue

class Server(object):
    
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.name = "Server"
        self.host = host if host is not None else '127.0.0.1'
        self.port = port
        self.address = (self.host, self.port)
        self.sock = None
        
    class ClientInstance(threading.Thread):
        def __init__(self, conn, addr, in_q):
            threading.Thread.__init__(self)
            self.name = "Client instance"
            self.client_conn = conn
            self.client_addr = addr
            self.in_q = in_q
            self.daemon = True
            
        def run(self):
            while True:
                data = self.client_conn.recv(255)
                
                print ("got message from {}".format(self.client_addr))
                
                if data.decode() == 'goodbye':
                    self.client_conn.send(b'farewell\n')
                    break
                elif data.decode() == 'exit':
                    self.client_conn.send(b'ok\n')
                    self.in_q.put('exit')
                    break
                elif data.decode() == 'hello':
                    self.client_conn.send(b'world\n')
                else:
                    self.client_conn.send(data + b'\n')
        
    def run_tcp_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(self.address)
            self.sock.settimeout(1)
            in_q = queue.Queue()
            self.sock.listen()
            i = 0
            
            while True and in_q.empty():
                try:
                    conn, address = self.sock.accept()
                except socket.timeout:
                    if not in_q.empty():
                        q_data = in_q.get()
                        break
                    continue

                print ("connection {} from {}".format(i, address))
                i = i + 1

                new_client_instance = self.ClientInstance(conn, address, in_q)
                new_client_instance.start()
                
        except Exception as exp:
            print ("The following exception raised during server execution: {}".format(exp))
        finally:
            self.sock.close()
            
    def run_udp_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(self.address)

            while True:
                data, address = self.sock.recvfrom(255)
                
                print ("got message from {}".format(address))
                
                if data.decode() == 'goodbye':
                    #data = b'farewell'
                    self.sock.sendto(b'farewell', address)
                elif data.decode() == 'exit':
                    self.sock.sendto(b'ok', address)
                    break
                elif data.decode() == 'hello':
                    #data = b'world'
                    self.sock.sendto(b'world', address)
                else:
                    self.sock.sendto(data, address)
        except Exception as exp:
            print ("The following exception raised during server execution: {}".format(exp))
        finally:
            self.sock.close()

class Client(object):
    
    def __init__(self, host, port):
        self.name = "Client"
        self.host = host
        self.port = port
        self.address = (host, port)
        self.sock = None
        
    def run_tcp_client(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(self.address)
            msg = input()
            
            while True:
                self.sock.sendall(bytes(msg,'UTF-8'))
                data =  self.sock.recv(255)
                print(data.decode())
                if msg in ['goodbye', 'exit']:
                    break
                msg = input()
        except Exception as exp:
            print ("The following exception raised during client execution: {}".format(exp))
        finally:
            self.sock.close()
            
    def run_udp_client(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = input()
            
            while True:
                self.sock.sendto(bytes(msg,'UTF-8'), self.address)
                data, address =  self.sock.recvfrom(255)
                #print("From Server at {}: {}".format(address, data.decode()))
                print(data.decode() + "\n")
                if msg in ['goodbye', 'exit']:
                    break
                msg = input()
    
        except Exception as exp:
            print ("The following exception raised during client execution: {}".format(exp))
        finally:
            self.sock.close()

