#!/bin/python

import socket
import sys
import time

debug = False

class Process():
    def __init__(self, index, ip, port):
        self.index = int(index)
        self.ip = ip
        self.port = port

class Server():
    def __init__(self, index, ip, port, hosts):
        self.index = int(index)
        self.ip = ip
        self.port = port
        self.hosts = hosts
        self.connections = {}
        self.state = 'Normal'
        self.election = False
        self.leader = max(self.hosts.keys())
        self.leaders = []
        self.prevleader = self.leader
        self.upList = []
        self.lasttime = int(time.time())
        self.lastack = -1
        for index, host in self.hosts.iteritems():
            self.upList.append(int(index))
        if debug:
            print "up: ", self.upList
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        if debug:
            print "starting"     
        while True:
            self.start()

    def leader_msg(self):
        data, addr = self.recv(1)
        if data != None and "leader" in data: # another process is leader
            #print data
            if self.data_to_index(data) > self.index:
                self.leader = self.data_to_index(data)
                print "[{0}] Node {1}: node {2} is elected as new leader.".format(getTime(), self.index, self.data_to_index(data))
                return
        for index, proc in self.hosts.iteritems():
            if index != self.index:
                if debug:
                    print "sending i am leader to {0}, up: {1}".format(index, self.upList)
                self.sock.sendto("{0} i am the leader".format(self.index), (proc.ip, proc.port))
        
        time.sleep(1)
    
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
                    return
                self.send_ok(self.data_to_index(data))
                self.no_leader()
            elif "leader" in data:
                if self.data_to_index(data) < self.index:
                    self.become_leader()
                    return

                if self.leader != self.data_to_index(data):
                    print "[{0}] Node {1}: node {2} is elected as new leader.".format(getTime(), self.index, self.data_to_index(data))

                self.leader = self.data_to_index(data)

                if self.prevleader != self.leader:
                    self.prevleader = self.leader

                self.send_ok(self.leader)
                if debug:
                    print "{0} is leader :)".format(self.data_to_index(data))
            elif "alive" in data:
                if debug:
                    print "alive??"

    def no_leader(self):
        print "[{0}] Node {1}: leader node {2} has crashed.".format(getTime(), self.index, self.leader)
        print "[{0}] Node {1}: begin another leader election.".format(getTime(), self.index, self.leader)
        self.election = False
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
            responses.append((data, addr))
        if debug:
            print responses
        if len(responses) == 0:
            self.become_leader()
            return
        else:
            ids = [-1]
            for res in responses:
                if res[0] == None:
                    continue
                s = int(res[0].split(' ')[0])
                if debug:
                    print s
                ids.append(s)
            if self.index >= max(ids):
                self.become_leader()
                return

    def become_leader(self):
        self.leader = self.index
        if self.prevleader != self.leader:

            print "[{0}] Node {1}: node {2} is elected as new leader.".format(getTime(), self.index, self.leader)
            self.prevleader = self.leader

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
        self.sock.sendto("{0} election".format(self.index), (proc.ip, proc.port))

    def send_ok(self, index):
        proc = self.hosts[index]
        self.sock.sendto("{0} ok".format(self.index), (proc.ip, proc.port))

    def addr_to_index(self, addr):
        for index, proc in self.hosts.iteritems():
            if proc.ip == addr[0]:
                return index
        return -1

    def data_to_index(self, data):
        return int(data.split(' ')[0])

def getTime():
    return time.strftime('%H:%M:%S', time.localtime())


def fillHosts(fileName, p):
    hosts = {}
    f = open(fileName)
    lines = f.read().strip().split('\n')
    for line in lines:
        line = line.split(' ')
        index = int(line[0])
        host = line[1]
        port = p
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
    hosts = fillHosts(args['-h'], port)
    ip = socket.gethostname()

    index = int(getIndex(ip, port, hosts))
    s = Server(index, ip, port, hosts)
    s.start()
