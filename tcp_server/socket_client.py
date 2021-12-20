# coding: utf-8
import socket
import time


message = 'heart beat'
server_address = ('localhost', 8090)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect thesocket to the port where the server is listening
print ('connecting to %s port %s' % server_address)
sock.connect(server_address)
while True:
    time.sleep(2)
    print ('%s: sending %s"' % (sock.getsockname(), message))
    sock.send(("client1:" + message).encode())
    data = sock.recv(1024)
    if data:
        print('{}: received from server '.format(sock.getsockname()))

print ('closing socket', sock.getsockname())
sock.close()
