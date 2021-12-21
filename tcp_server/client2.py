import socket
import time

class MiniClient:

    def __init__(self, host='localhost', port=8090):
        self.message = 'hello~'
        self.server_address = (host, port)
        self.count = 0
        self.time_lapse = 2
        self.send_msg = 2
        self.last_write_time = 0
        self.max_waiting_time = 50
        self.sock = None

    def connect(self):
        # Create a TCP/IP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect thesocket to the port where the server is listening
        print ('connecting to %s port %s' % self.server_address)
        self.sock.connect(self.server_address)

    def run(self):
        self.connect()
        count = 0
        while True:
            time.sleep(self.time_lapse)
            if count < self.send_msg:
                self.sock.send((self.message).encode())
            data = self.sock.recv(1024)
            if data:
                print('{}: received from server, msg [{}] '.format(self.sock.getsockname(), data.decode()))
                self.last_write_time = time.time()
            if time.time() - self.last_write_time > self.max_waiting_time:
                print('No response for {}s, exit.'.format(self.max_waiting_time))
                break
            count += 1

        print('closing socket', self.sock.getsockname())
        self.sock.close()


if __name__ == '__main__':
    client = MiniClient()
    client.run()