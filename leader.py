#!/bin/python

import socket
import sys

hosts = []
args = {}
value = 0

ip = "127.0.0.1"
port = 1337 #default

class Process():
    def __init__(self, index, ip, port):
        self.index = index
        self.ip = ip
        self.port = port

    def __str__(self):
        return "{0} {1} {2}".format(self.index, self.ip, self.port)

def fillHosts(fileName):
    f = open(fileName)
    lines = f.read().strip().split('\n')
    for line in lines:
        line = line.split(' ')
        if int(line[2]) == port:
            continue
        hosts.append(Process(int(line[0]), line[1], int(line[2])))

def propose(i):
    sock = socket.socket(socket.AF_INET,
            socket.SOCK_DGRAM)
    sock.bind((ip, port))
    for h in hosts:
        sock.sendto(str(i), (h.ip, h.port))
    while True:
        data, addr = sock.recvfrom(1024)
        print data


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2:
        args[a[0]] = a[1]
    if len(a) >= 4:
        args[a[2]] = a[3]
    if len(a) >= 6:
        args[a[4]] = a[5]
    port = int(args['-p'])
    fillHosts(args['-h'])
    propose(5)
