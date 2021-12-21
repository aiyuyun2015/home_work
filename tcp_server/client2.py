# coding: utf-8
import socket
import time


message = 'hello~'
server_address = ('localhost', 8090)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect thesocket to the port where the server is listening
print ('connecting to %s port %s' % server_address)
sock.connect(server_address)
count = 0

while True:
    time.sleep(2)
    if count < 2:
        sock.send((message).encode())
    data = sock.recv(1024)
    if data:
        print('{}: received from server, msg [{}] '.format(sock.getsockname(), data.decode()))
    count += 1
while True:
    pass
print ('closing socket', sock.getsockname())
sock.close()
