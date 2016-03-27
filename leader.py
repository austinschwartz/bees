#!/bin/python

import socket
import sys
import time

debug = True

class Process():
    def __init__(self, index, ip, port):
        self.index = int(index)
        self.ip = ip
        self.port = port

class Server():
    def __init__(self, index, ip, port, hosts):
        self.index = index
        self.ip = ip
        self.port = port
        self.hosts = hosts
        self.connections = {}
        self.state = 'Normal'
        self.leader = max(self.hosts.keys())
        self.prevleader = self.leader
        self.upList = []
        for index, host in self.hosts.iteritems():
            self.upList.append(int(index))
        if debug:
            print "up: ", self.upList
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        
        self.start()
        pass

    def leader_msg(self):
        data, addr = self.recv(1)
        if data != None and "leader" in data: # another process is leader
            if self.addr_to_index(addr) > self.index:
                self.leader = self.addr_to_index(addr)
                return
        for index, proc in self.hosts.iteritems():
            if index != self.index:
                if self.prevleader != self.leader:
                    print "[{0}] Node {1}: node {2} is elected as new leader.".format(getTime(), self.index, self.leader)
                    self.prevleader = self.leader

                if debug:
                    print "sending i am leader to {0}, up: {1}".format(index, self.upList)
                self.sock.sendto("{0}: i am the leader".format(self.index), (proc.ip, proc.port))
        
        time.sleep(1)
        self.start()
    
    def start(self):
        responses = []
        if self.leader == self.index:
            self.leader_msg()
        else:
            data, addr = self.recv(3) # timeout = 3 seconds
            if data == None: # at this point, there is no coordinator
                self.no_leader()
            elif "election" in data:
                if max(self.upList) == self.index:
                    self.become_leader()
                self.send_ok(self.addr_to_index(addr))
                self.no_leader()
            elif "leader" in data:
                if self.addr_to_index(addr) < self.index:
                    return
                if self.leader != self.addr_to_index(addr):
                    self.leader = self.addr_to_index(addr)
                if self.leader != self.prevleader:
                    self.prevleader = self.leader
                    print "[{0}] Node {1}: node {2} is elected as new leader.".format(getTime(), self.index, self.leader)
                self.send_ok(self.leader)
                if debug:
                    print "{0} is leader :)".format(self.addr_to_index(addr))
            elif "alive" in data:
                if debug:
                    print "alive??"
            self.start()

    def no_leader(self):
        print "[{0}] Node {1}: leader node {2} has crashed.".format(getTime(), self.index, self.leader)
        if int(self.leader) in self.upList:
            self.upList.remove(int(self.leader))
        for index, proc in self.hosts.iteritems():
            if index > self.index:
                self.send_election(index)

        data = ""
        addr = ""
        # collect responses
        responses = []
        while data != None:
            data, addr = self.recv()
            responses += (data, addr)
        print responses
        if len(responses) == 0:
            self.become_leader()
        else:
            if max(self.upList) == self.index:
                self.become_leader()


    def become_leader(self):
        self.leader = self.index
        if self.prevleader != self.leader:
            print "[{0}] Node {1}: node {2} is elected as new leader.".format(getTime(), self.index, self.leader)
            self.prevleader = self.leader
        self.start()

    def recv(self, t=2):
        self.sock.settimeout(t)
        try:
            data, addr = self.sock.recvfrom(1024)
        except socket.timeout:
            if debug:
                print "Timeout!"
            return None, None

        self.sock.settimeout(None)
        return data, addr

    def send_election(self, index):
        proc = self.hosts[index]
        self.sock.sendto("election from {0}".format(self.index), (proc.ip, proc.port))

    def send_ok(self, index):
        proc = self.hosts[index]
        self.sock.sendto("ok from {0}".format(self.index), (proc.ip, proc.port))

    def addr_to_index(self, addr):
        for index, proc in self.hosts.iteritems():
            if proc.ip == addr[0] and int(proc.port) == int(addr[1]):
                return index
        return -1

def getTime():
    return time.strftime('%H:%M:%S', time.localtime())


def fillHosts(fileName):
    hosts = {}
    f = open(fileName)
    lines = f.read().strip().split('\n')
    for line in lines:
        line = line.split(' ')
        index = int(line[0])
        host = line[1]
        port = int(line[2])
        hosts[index] = Process(index, host, port)
    return hosts

def getIndex(ip, port, hosts):
    for index, proc in hosts.iteritems():
        if proc.ip == ip and proc.port == port:
            return int(index)
    return -1

if __name__ == '__main__':
    a = sys.argv[1:]
    args = {}
    if len(a) >= 2:
        args[a[0]] = a[1]
    if len(a) >= 4:
        args[a[2]] = a[3]
    if len(a) >= 6:
        args[a[4]] = a[5]
    port = int(args['-p'])
    hosts = fillHosts(args['-h'])
    #
    #for index, proc in hosts:
    #    # update later
    #    if proc.port == port:
    # addr = socket.gethostbyname(socket.gethostname()
    ip = "127.0.0.1"
    index = getIndex(ip, port, hosts)
    s = Server(index, ip, port, hosts)
    s.start()
