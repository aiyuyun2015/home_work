# coding: utf-8
import select
import socket
import time
from time import sleep
import multiprocessing
from collections import defaultdict

try:
    import queue
except ImportError:
    import Queue as queue


class MiniServer:

    def __init__(self):
        self.inputs = []
        self.outputs = [] # write to
        self.message_queues = {} #outgoing message
        self.max_clients = 5
        self.ip = 'localhost'
        self.port = 8090
        self.heartbeat_rate = 3
        self.heartbeat_msg = b'heart beat test from server'
        self.last_write_time = {}
        self.heartbeat_interval = 10
        self.failed_connection = defaultdict(int)
        self.max_failure = 1

    def connect(self):
        # Create a TCP/IP
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)

        # Bind the socket to the port
        server_address = (self.ip, self.port)
        print ('starting up on %s port %s' % server_address)
        self.server.bind(server_address)
        # Listen for incoming connections
        self.server.listen(self.max_clients)

        # Sockets from which we expect to read
        self.inputs = [self.server]


    def disconnect(self, s):
        if s in self.outputs:
            self.outputs.remove(s)
            self.inputs.remove(s)
            s.close()

            # Remove message queue
            del self.message_queues[s]


    def run(self):
        self.connect()
        count = 0
        print("waiting for connect...")

        while self.inputs:
            count += 1
            # Wait for at least one of the sockets to be ready for processing
            # print ('waiting for the next event')
            #print("iteration{}".format(count))
            #print(self.inputs)
            #print("waiting for connect...")
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            # Handle inputs
            for s in readable:
                if s is self.server:
                    # A "readable" socket is ready to accept a connection
                    connection, client_address = s.accept()
                    print('connection from', client_address)
                    # this is connection not server
                    connection.setblocking(0)
                    self.inputs.append(connection)

                    # Give the connection a queue for data we want to send
                    self.message_queues[connection] = queue.Queue()
                else:
                    #print("Ready for reading client's data")
                    try:
                        data = s.recv(1024)
                    except:
                        print("disconnected.")
                        self.disconnect(s)
                        writable = []
                        continue
                    # client send msg to server
                    if data != b'':
                        # A readable client socket has data
                        print ('received msg[{}] from {}\n'.format(data.decode(), s.getpeername()))
                        self.message_queues[s].put(data)
                        # Add output channel for response
                        if s not in self.outputs:
                            self.outputs.append(s)
                    # client send empty to server when it's disconnected
                    else:
                        #print("Receiving empty from client")
                        print ('client {} disconnect, closing.'.format(client_address))
                        # Stop listening for input on the connection
                        self.disconnect(s)

            for s in writable:
                # write to client if there are data
                # otherwise write heart beat
                # after write, make a record
                # the curr write - prev write time > interval
                # remove the list!
                message_queue = self.message_queues.get(s)
                send_data = ''
                if message_queue is None:
                    continue
                if not message_queue.empty():
                    send_data = message_queue.get_nowait()
                else:
                    time.sleep(self.heartbeat_rate)
                    curr = time.time()
                    if curr - self.last_write_time[s] > self.heartbeat_interval:
                        print("haven't receive data from {} for more than  {}s".
                              format(client_address, self.heartbeat_interval))
                        send_data = self.heartbeat_msg
                    else:
                        continue

                print('send msg [{}] to {}\n'.format(send_data.decode(), client_address))
                # print(s)
                send_ret = s.send(send_data)

                if send_ret > 0:
                    self.last_write_time[s] = time.time()
                    self.failed_connection[s] = 0
                else:
                    self.failed_connection[s] += 1
                    if self.failed_connection[s] > self.max_failure:
                        print("Client no response, disconnect")
                        self.disconnect(s)

            # # Handle "exceptional conditions"
            for s in exceptional:
                print ('exception condition on', s.getpeername())
                # Stop listening for input on the connection
                self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                s.close()

                # Remove message queue
                del self.message_queues[s]



if __name__ == '__main__':
    server = MiniServer()
    multiprocessing.Process(target=server.run, args=()).start()