# -*- coding: utf-8 -*-
import socket
import struct

from django.conf import settings

class Socket(object):
    def __init__(self, address=None):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.address = settings.TSUMEGO_SOCKET_ADDRESS if address is None else address

    def __enter__(self):
        self.socket.connect(self.address)
        return self.socket

    def __exit__(self, type, value, traceback):
        self.socket.close()

def send_int(socket, value, fmt="i"):
    socket.send(struct.pack(fmt, value))

def receive(socket, fmt):
    return socket.recv(struct.calcsize(fmt))

def receive_int(socket, fmt="i"):
    return struct.unpack(fmt, receive(socket, fmt))[0]

def receive_str(socket):
    str_len = receive_int(socket)
    return socket.recv(str_len)
