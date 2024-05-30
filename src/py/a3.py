##################################################
# File name:    a3.py (both part 1 & part 2)     #  
# Desceription: RUDP Assignment                  #
# Author:       Paventhan Vivekanandan           #
# mail-id:      pvivekan@iu.edu                  #
# Course:       Computer Networks [P538]         #
##################################################

#!/usr/bin/env python3

import sys
import socket
import threading
import queue
import time

# class implementing reliable data transfer
class ReliableDataTransfer(object):
    
    ##########################################################################################
    # Fields:										        #
    # -------										        #
    # expectedSeqNum: indicates the next sequence number expected by the reciever		#
    # nextSeqNum: indicates the next sequence number to send					#
    # rcvSeqNum: indicates the received sequence number					#
    # msgType: takes 3 values									#
    #    A - acknowledgment, 									#
    #    D - data, 										#
    #    F - Finish (client sends data type 'F' to indicate completion of file transfer)	#
    # sock: stores socket handler								#
    # buf: stores file handler 								#
    #												#
    #########################################################################################
    
    def __init__(self):
        self.expectedSeqNum = 0
        self.nextSeqNum = 0
        self.rcvSeqNum = None
        self.msgType = None
        self.sock = None
        self.buf = None
        self.window_size = 500
        self.cwnd = 50
        self.max_cwnd_size = int(self.window_size * 0.95)
        self.seqNumLmt = 3 * self.window_size
        self.base = 0

    # reliable data transfer sender implementation (functions on top of unreliable channel)
    def rdt_send(self, msg, addr):
        send = 0
        MSS = 10 # setting MSS to 10 bytes
        st = 0
        end = MSS
        self.expectedSeqNum = self.nextSeqNum
        send_data = True
        timeout = 0.01
        transfer_complete = False
        FIN_cnt = 0
        
        print ("File transfer in progress... Please wait...")

        while send < len(msg) or transfer_complete:
            if send_data:
                if not transfer_complete:
                    self.msgType = 'D'
                    header = self.msgType + str(self.nextSeqNum)
                    data = header + msg[st:end]
                else:
                    self.msgType = 'F'
                    header = self.msgType + str(self.nextSeqNum)
                    data = header
                    FIN_cnt = FIN_cnt + 1
                
                self.sock.sendto(bytes(data, 'UTF-8'), addr)
                
                # send FIN for 10 timeouts and then exit
                if FIN_cnt > 10:
                    return len(msg)

            #print ("timeout -> ", timeout)
            self.sock.settimeout(timeout)
                
            try:
                start_time = time.time()
                data, addr = self.sock.recvfrom(255)
                data = data.decode()
                self.msgType = data[0]
                self.rcvSeqNum = int(data[1])
                data = data[2:]
                    
                stop_time = time.time()
                    
                if self.rcvSeqNum == self.expectedSeqNum and (self.msgType == 'A' or self.msgType == 'F'):
                    send = send + 10
                    st = end
                    end = end + MSS
                    
                    if self.msgType == 'F':
                        return len(msg)
                    
                    if send >= len(msg):
                        transfer_complete = True
                    
                    self.nextSeqNum = (self.nextSeqNum + 1) % 2
                    self.expectedSeqNum = self.nextSeqNum
                    timeout = 0.01
                    send_data = True
                else:
                    timeout = timeout - (stop_time - start_time)
                    if timeout > 0:
                        send_data = False
                    else:
                        send_data = True
                        timeout = 0.01
                    #print ("out of order packet received !")
            # handling timeout
            except socket.timeout:
                #print ("timeout occurred !")
                send_data = True
                     
        return len(msg)

    # reliable data transfer receiver implementation (functions on top of unreliable channel)
    def rdt_rcv(self, buf_size):
        
        client_closed = False
        client_connected = False
        
        while True:
            data, addr = self.sock.recvfrom(buf_size)
            data = data.decode()
            self.msgType = data[0]
            self.rcvSeqNum = int(data[1])
            msg = data[2:]
                    
            #print ("msg recvd -> ", msg, " rseq -> ", self.rcvSeqNum, " eseq -> ", self.expectedSeqNum)
                
            if self.msgType == 'D' and self.rcvSeqNum == self.expectedSeqNum:
            
                if not client_connected:
                    print ("File transfer in progress... Please wait...")
                    client_connected = True
            
                self.buf.write(msg)
                self.expectedSeqNum = (self.expectedSeqNum + 1) % 2
                self.msgType = 'A'
            elif self.msgType == 'F':
                if not client_closed:
                    print ("File transfer is completed !")
                client_closed = True
                self.buf.close()
            else:
                self.msgType = 'A' # out-of-order packet received. Acknowledge last valid packet received.
                #print ("out of order packet received !")

            data = self.msgType + str(self.rcvSeqNum)
            data = bytes(data, 'UTF-8')
            self.sock.sendto(data, addr)
            
            if self.msgType == 'F':
                return

    # reliable data transfer sender implementation (functions on top of unreliable channel)
    def go_back_N_send(self, msg, addr):
        send = 0
        MSS = 1024 # setting MSS to 1024 bytes
        st = 0
        end = MSS
        send_data = True
        timeout = 0.0005
        transfer_complete = False
        last_ack_received = False
        window = {}
        self.nextSeqNum = 0
        tmo_cnt = 0
        
        print ("File transfer in progress... Please wait...")

        while (send < len(msg)) or transfer_complete:
            while (self.nextSeqNum < ((self.base+self.window_size) % self.seqNumLmt)) or \
                  ((self.nextSeqNum > self.base) and (((self.base+self.window_size) >= self.seqNumLmt) or (self.nextSeqNum < self.base+self.window_size))):
            
                last_byte_ack = self.base
                last_byte_send = self.nextSeqNum
                total_send = 0
                
                if last_byte_send < last_byte_ack:
                    w_end = self.seqNumLmt - last_byte_ack
                    total_send = w_end + last_byte_send - 1
                else:
                    total_send = last_byte_send - last_byte_ack
                    
                if self.cwnd <= total_send:
                    break
            
                #if send_data:
                if len(str(self.nextSeqNum)) == 1:
                    self.nextSeqNum = "000" + str(self.nextSeqNum)
                elif len(str(self.nextSeqNum)) == 2:
                    self.nextSeqNum = "00" + str(self.nextSeqNum)
                elif len(str(self.nextSeqNum)) == 3:
                    self.nextSeqNum = "0" + str(self.nextSeqNum)
                
                if not transfer_complete and send < len(msg):
                    self.msgType = 'D'
                    header = self.msgType + str(self.nextSeqNum)
                    data = header + msg[st:end]
                    send = send + 1024
                    st = end
                    end = end + MSS
                        
                    if send >= len(msg):
                        last_msg_seqNum = (int(self.nextSeqNum) + 1) % self.seqNumLmt
                        transfer_complete = True
                elif transfer_complete and last_ack_received == True and self.base == int(self.nextSeqNum):
                    FIN_timeout = 1
                    while FIN_timeout < 10:
                        self.msgType = 'F'
                        header = self.msgType + str(self.nextSeqNum)
                        data = header
                        pkt = bytes(data, 'UTF-8')
                        self.sock.sendto(pkt, addr)
                    
                        try:
                            data, addr = self.sock.recvfrom(255)
                            data = data.decode()
                            self.msgType = data[0]
                    
                            if self.msgType == 'F':
                                #print ("Received FIN from server. Exiting !")
                                return len(msg)
                        except socket.timeout:
                            FIN_timeout = FIN_timeout + 1
                            continue
                            
                    #print ("FIN timeout expired. Exiting !")
                    return len(msg)
                else:
                    send_data = False
                    self.nextSeqNum = int(self.nextSeqNum)
                    break
                        
                self.nextSeqNum = int(self.nextSeqNum)
                if send_data == True:
                    pkt = bytes(data, 'UTF-8')
                    self.sock.sendto(pkt, addr)
                    
                    window[self.nextSeqNum] = pkt
                    #print ("sending pkt seq -> {}".format(self.nextSeqNum))
                    self.nextSeqNum = (self.nextSeqNum + 1) % self.seqNumLmt
                    
                    if transfer_complete:
                        send_data = False

            self.sock.settimeout(timeout)
                
            try:
                data, addr = self.sock.recvfrom(255)
                data = data.decode()
                self.msgType = data[0]
                self.rcvSeqNum = int(data[1:5])
                data = data[5:]
                    
                self.base = (self.rcvSeqNum + 1) % self.seqNumLmt
                #print ("received ack pkt seqNum -> {}, base -> {}".format(self.rcvSeqNum, self.base))
                
                # still unacknowledged packets exists in the window
                if self.base != self.nextSeqNum:
                    timeout = 0.0005
                
                # slow start: increase congestion window size by 10 for every successfull acks
                self.cwnd = self.cwnd + 10
                
                if self.cwnd > self.window_size:
                    self.cwnd = self.window_size
                
                if self.msgType == 'F':
                    #print ("received FIN from server. Exiting !")
                    return len(msg)
                        
                if transfer_complete:
                    if self.base == last_msg_seqNum: #self.nextSeqNum: # or self.base == last_msg_seqNum:
                        last_ack_received = True
                    
            # handling timeout
            except socket.timeout:
                #print ("timeout occurred ! base -> {}, nextSeqNum -> {}".format(self.base, self.nextSeqNum))
                tmo_cnt = tmo_cnt + 1 

                # wait for 5 timeouts to change congestion window size
                if tmo_cnt > 10:
                    # multiplicative decrease of congestion window size on timeout
                    self.cwnd = int(self.cwnd * 0.75)
                
                    if self.cwnd < 50:
                        self.cwnd = 50
                        
                    tm0_cnt = 0
                                
                cwnd_adj = self.window_size - self.cwnd
                #print ("cwnd -> {}, cwnd adjusted -> {}".format(self.cwnd, cwnd_adj))
                    
                if self.base < self.nextSeqNum:
                
                    # check if within congestion limit or atleast send 3 pkts. 
                    # otherwise both server and client gets blocked due to 0 pkt transmission
                    if (self.nextSeqNum - self.base) < self.cwnd or (self.nextSeqNum - self.base) <= 50:
                        for i in range(self.base, self.nextSeqNum):
                            #print ("sending pkt -> {}".format(i))
                            self.sock.sendto(window[i], addr)
                    else:
                        for i in range(self.base, self.base+50):
                            #print ("sending pkt -> {}".format(i))
                            self.sock.sendto(window[i], addr)
                elif self.base > self.nextSeqNum:

                    w_end = self.seqNumLmt - self.base
                    total_send = w_end + self.nextSeqNum - 1
                        
                    if total_send < self.cwnd or total_send <= 50:
                        for i in range(self.base, self.seqNumLmt):
                            #print ("sending pkt -> {}".format(i))
                            self.sock.sendto(window[i], addr)
                            
                        for i in range(0, self.nextSeqNum):
                            #print ("sending pkt -> {}".format(i))
                            self.sock.sendto(window[i], addr)
                    else:        
                            
                        if self.base+50 < self.seqNumLmt:
                            for i in range(self.base, self.base+50):
                                #print ("sending pkt -> {}".format(i))
                                self.sock.sendto(window[i], addr)
                        else:
                            for i in range(self.base, self.seqNumLmt):
                                #print ("sending pkt -> {}".format(i))
                                self.sock.sendto(window[i], addr)
                            for i in range(0, 50 - (self.seqNumLmt - self.base)):
                                #print ("sending pkt -> {}".format(i))
                                self.sock.sendto(window[i], addr)
                     
        return len(msg)

    # reliable data transfer receiver implementation (functions on top of unreliable channel)
    def go_back_N_rcv(self, buf_size):
        
        client_closed = False
        client_connected = False
        correctly_received_SeqNum = 0

        while True:
            data, addr = self.sock.recvfrom(buf_size)
            data = data.decode()
            self.msgType = data[0]
            self.rcvSeqNum = int(data[1:5])
            msg = data[5:]
                    
            #print ("msg recvd -> ", msg, " rseq -> ", self.rcvSeqNum, " eseq -> ", self.expectedSeqNum)
                
            if self.msgType == 'D' and self.rcvSeqNum == self.expectedSeqNum:
            
                if not client_connected:
                    print ("File transfer in progress... Please wait...")
                    client_connected = True
            
                self.buf.write(msg)
                #print ("expected packet received ! recSeqNum -> {}, expSeqNum -> {}".format(self.rcvSeqNum, self.expectedSeqNum))
                correctly_received_SeqNum = self.expectedSeqNum
                self.expectedSeqNum = (self.expectedSeqNum + 1) % self.seqNumLmt
                self.msgType = 'A'
            elif self.msgType == 'F' and self.rcvSeqNum == self.expectedSeqNum:
                #print ("FIN from client received !")
                if not client_closed:
                    print ("File transfer is completed !")
                client_closed = True
                self.buf.close()
                return
            else:
                #print ("out of order packet received ! recSeqNum -> {}, expSeqNum -> {}".format(self.rcvSeqNum, self.expectedSeqNum))
                self.msgType = 'A' # out-of-order packet received. Acknowledge last valid packet received.
                self.rcvSeqNum = correctly_received_SeqNum

            #print ("sending ack for {}".format(self.rcvSeqNum))
            
            if len(str(self.rcvSeqNum)) == 1:
                self.rcvSeqNum = "000" + str(self.rcvSeqNum)
            elif len(str(self.rcvSeqNum)) == 2:
                self.rcvSeqNum = "00" + str(self.rcvSeqNum)
            elif len(str(self.rcvSeqNum)) == 3:
                self.rcvSeqNum = "0" + str(self.rcvSeqNum)
            
            data = self.msgType + str(self.rcvSeqNum)
            data = bytes(data, 'UTF-8')
            self.sock.sendto(data, addr)


# class implementing server
class Server(object):
    
    def __init__(self, host, port, file_handle):
        threading.Thread.__init__(self)
        self.name = "Server"
        self.host = host if host is not None else '127.0.0.1'
        self.port = port
        self.address = (self.host, self.port)
        self.sock = None
        self.file = file_handle
        self.rdt = ReliableDataTransfer()
    
    # support for multi-threading
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
        
    # tcp server implementation
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
            
    # udp server implementation
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
    
    # reliable udp server/receiver implementation        
    def run_rudp_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rdt.sock = self.sock
            self.sock.bind(self.address)

            #fh = open(self.file, 'w')
            self.rdt.buf = self.file
            self.rdt.rdt_rcv(255)
                
        except Exception as exp:
            print ("The following exception raised during server execution: {}".format(exp))
        finally:
            self.sock.close()
    
    # udp server implementation for file (invoking this will lose data)      
    def run_udp_server_file(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rdt.sock = self.sock
            self.sock.bind(self.address)

            seqNum = 0

            while True:
                msg, address = self.sock.recvfrom(255)
                
                if msg.decode() == "EOF":
                    self.file.close()
                    print ("File transfer is completed !")
                else:
                    self.file.write(msg.decode())
                    
        except Exception as exp:
            print ("The following exception raised during server execution: {}".format(exp))
        finally:
            self.sock.close()

    # go-back-N server/receiver implementation        
    def run_gbn_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rdt.sock = self.sock
            self.sock.bind(self.address)

            #fh = open(self.file, 'w')
            self.rdt.buf = self.file
            self.rdt.go_back_N_rcv(1600)
                
        except Exception as exp:
            print ("The following exception raised during server execution: {}".format(exp))
        finally:
            self.sock.close()

# class implementing client
class Client(object):
    
    def __init__(self, host, port, file_handle):
        self.name = "Client"
        self.host = host
        self.port = port
        self.address = (host, port)
        self.sock = None
        self.file = file_handle
        self.rdt = ReliableDataTransfer()
        
    # tcp client implementation
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
    
    # udp client implementation        
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
            
    # reliable udp client/sender implementation
    def run_rudp_client(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rdt.sock = self.sock
            
            #with open(self.file, 'r') as fh:
            msg = self.file.read()
            
            print ("msg length -> ", len(msg))
            send = self.rdt.rdt_send(msg, self.address)
            print ("File transfer is completed !")
            print ("msg send length -> ", send)
    
        except Exception as exp:
            print ("The following exception raised during client execution: {}".format(exp))
        finally:
            self.sock.close()

    # udp client implementation (invoking this will lose data)
    def run_udp_client_file(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rdt.sock = self.sock
            timeout = 1.0

            msg = self.file.read()
            
            print ("msg length -> ", len(msg))
            send = 0
            st = 0
            end = 10
            
            while send < len(msg):
                self.sock.sendto(bytes(msg[st:end], 'UTF-8'), self.address)
                send = send + 10
                st = end
                end = end + 10
                    
            print ("msg send len -> ", send)
            self.sock.sendto(bytes("EOF", 'UTF-8'), self.address)
    
        except Exception as exp:
            print ("The following exception raised during client execution: {}".format(exp))
        finally:
            self.sock.close()

    # go-back-N client/sender implementation
    def run_gbn_client(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rdt.sock = self.sock
            
            #with open(self.file, 'r') as fh:
            msg = self.file.read()
            
            print ("msg length -> ", len(msg))
            send = self.rdt.go_back_N_send(msg, self.address)
            print ("File transfer is completed !")
            print ("msg send length -> ", send)
    
        except Exception as exp:
            print ("The following exception raised during client execution: {}".format(exp))
        finally:
            self.sock.close()
            
