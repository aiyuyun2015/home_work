#!/usr/bin/env python3

import socket

HOST = '0.0.0.0'  # The server's hostname or IP address
#PORT = 55556        # The port used by the server
PORT = 8090       # The port used by the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect_ex((HOST, PORT))
    while True:
        s.sendall(b'Hello, world')
        data = s.recv(1024)

        print('Received', repr(data))