#!/usr/bin/env python
# -*- coding:utf-8 -*-
import socket
import select
import time
import multiprocessing

time.clock = time.time

HOST = '127.0.0.1'
PORT = 8090
BUF_SIZE = 8096

class param:
    def __init__(self):
        ipc_queue = None
        message_queues = None
        client_socket_fd_map = None
        client_socket_heartbeat_map = None
        inputs = None
        outputs = None
        m = None


def web_socket_init():
    param.message_queues = param.m.dict()
    param.client_socket_fd_map = param.m.dict()
    param.ipc_queue = param.m.Queue()


def ipc_queue_receive(mq, ipc_q):
    param.message_queues = mq
    param.ipc_queue = ipc_q
    while True:
        data = param.ipc_queue.get(block=True)
        fd = int(data[0])
        msg = data[1]
        if fd in param.message_queues.keys():
            param.message_queues[fd].put(msg)


def start_socket_select_server(mq, client_socket_fd_map):

    m = multiprocessing.Manager()
    param.message_queues = mq
    param.inputs = []
    param.outputs = []

    socketserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socketserver.bind((HOST, PORT))
    socketserver.listen(5)
    print('websocket monitoring:', (HOST, PORT))
    param.inputs.append(socketserver)

    # init heart beat
    param.client_socket_fd_map = client_socket_fd_map
    param.client_socket_heartbeat_map = {}
    heartbeat_check_time = time.clock()
    heartbeat_check_intervel_sec = 1

    while True:
        readable, writeable, exceptional = select.select(param.inputs, param.outputs, param.inputs)
        for s in readable:
            if s is socketserver:
                conn, address = socketserver.accept()
                print('new connection from:', address)
                param.inputs.append(conn)
                q = m.Queue()
                param.message_queues[conn.fileno()] = q
            else:
                if s not in param.outputs and s in param.inputs:
                    data = s.recv(1024)
                    if data:
                        if s not in param.outputs:
                            param.outputs.append(s)
                            param.client_socket_fd_map[s.fileno()] = s
                    else:
                        disconnect(s.fileno(),param.client_socket_fd_map)
                else:
                    try:
                        info = s.recv(BUF_SIZE)
                    except Exception as e:
                        info = None
                    if info:
                        if param.client_socket_heartbeat_map[s.fileno()]['c'] > 0:
                            param.client_socket_heartbeat_map[s.fileno()]['c'] -= 1
                    else:
                        disconnect(s.fileno(), param.client_socket_fd_map)

        while True:
            write_doing_flag = True
            for s in writeable:
                w_fd = s.fileno()
                if w_fd not in param.message_queues.keys():
                    continue
                if not param.message_queues[w_fd].empty():
                    next_msg = param.message_queues[w_fd].get_nowait()
                    send_ret = s.send(next_msg.encode())
                    if w_fd not in param.client_socket_heartbeat_map.keys():
                        param.client_socket_heartbeat_map[w_fd] = {}
                    if send_ret > 0:
                        param.client_socket_heartbeat_map[w_fd]['w'] = time.clock()
                        param.client_socket_heartbeat_map[w_fd]['c'] = 0

                    write_doing_flag = False
            if write_doing_flag:
                break

        cur = time.clock()
        if cur - heartbeat_check_time > heartbeat_check_intervel_sec:
            heartbeat_check_time = cur
            tmp = param.client_socket_heartbeat_map.copy()
            for k, v in tmp.items():
                write_delta = cur - v['w']
                count = v['c']
                if count > 10:
                    print('k: %s, v: %s, cur: %s, write_delta: %s,' % (k, v, cur, write_delta))
                    disconnect(k, param.client_socket_fd_map)
                elif write_delta > heartbeat_check_intervel_sec:
                    msg = 'heart test'
                    param.client_socket_fd_map[k].send(msg.encode())
                    param.client_socket_heartbeat_map[k]['c'] += 1


def disconnect(fd, fd_map):
    if fd in fd_map:
        print('client [%s] closed' % fd)
        print('Client disconnected')
        sock = fd_map[fd]
    else:
        return
    if sock in param.outputs:
        param.outputs.remove(sock)
    elif len(param.outputs) > 0:
        param.outputs.pop()
    if fd in param.message_queues: del param.message_queues[fd]
    if fd in param.client_socket_fd_map: del param.client_socket_fd_map[fd]
    if fd in param.client_socket_heartbeat_map: del param.client_socket_heartbeat_map[fd]

    if sock in param.inputs:
        param.inputs.remove(sock)
    elif len(param.inputs) > 0:
        param.inputs.pop()
    sock.close()


if __name__ == '__main__':
    param.m = multiprocessing.Manager()
    web_socket_init()

    multiprocessing.Process(target=start_socket_select_server,
                            args=(param.message_queues, param.client_socket_fd_map)).start()

    multiprocessing.Process(target=ipc_queue_receive,
                            args=(param.message_queues, param.ipc_queue)).start()

    while True:
        time.sleep(1)
        for fd in param.client_socket_fd_map.keys():
            param.ipc_queue.put((fd, "heart beat"))


