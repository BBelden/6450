#!/usr/bin/env python3

## Name:        Ben Belden
## Class ID#:   bpb2v
## Section:     CSCI 6450-001
## Assignment:  Lab #2
## Due:         18:00:00, February 28, 2017
## Purpose:     Write a simple interpreter that namesures a described virtual network 
##			    of switches, routers, and hosts, and then requests that specified 
##              operations be executed on those systems.
## Input:       From preformatted file.  
## Outut:       To terminal.
## 
## File:        p2.py

import os				# fork()
import sys				# argv[]
import socket			# UNIX socket()
import select			# UNIX select()
import pickle  			# byte streams
from time import sleep  # sleep()

def BeVS(d, dev2mac, dev2name, dev2net, mac2dev, mac2ip, mac2net, net2mac):
    done = False
    stop = False
    scktList = []
    for n in net2mac[dev2net[d]]: scktList.append(n[1][1])
    scktList.append(dev2name[d][1][1]) 
    
    while not done:
        (sckt, unused, unused) = select.select(scktList, [], [], 30)

        for s in sckt:
            pkt = pickle.loads(s.recv(255))

            if(pkt[0] == 'STOP'): stop = True
            else:
                sendSckt = None 
                for n in net2mac:
                    if sendSckt == None:
                        for m in net2mac[n]:
                            if pkt[3] == m[0]: 
                                sendSckt = m[1][1]
                                break

                if pkt[3] == '255':
                    for n in net2mac[dev2net[d]]: n[1][1].send(pickle.dumps(pkt[1:]))
                elif dev2net[d] != mac2ip[pkt[3]].split('.')[0]:
                    print("BAD SEND: to " + pkt[3] + " from " + d)
                    continue
                else:   
                    if mac2ip[pkt[2]].split('.')[0] == mac2ip[pkt[3]].split('.')[0]:
                        sendSckt.send(pickle.dumps(pkt[1:]))

        if stop:
            done = True
            break
#end BeVS


def BeVRVH(d, dev2mac, dev2name, dev2net, mac2dev, mac2ip, mac2net, net2mac):
    done = False
    stop = False
    scktList = []
    scktList.append(dev2name[d][1][1]) 

    for n in dev2name:
        if dev2name[n][0] == 'vs':
            for m in net2mac[dev2net[n]]:
                if m[0] in dev2mac[d]: scktList.append(m[1][0])

    while not done:
        (sckt, unused, unused) = select.select(scktList, [], [], 30)

        for s in sckt:
            pkt = pickle.loads(s.recv(255))
            if(pkt[0] == 'STOP'): stop = True
            else:
                if pkt[0] == 'macsend':
                    print("macsend from from_" + d + " to to_" + pkt[3] + ": " + pkt[1])
                    netSend = mac2ip[pkt[2]].split('.')[0] 
                    sendSckt = None 
                    for i in net2mac:
                        if sendSckt == None:
                            for x in net2mac[i]:
                                if pkt[2] == x[0]: 
                                    sendSckt = x[1][0]
                                    break
                    if sendSckt != None: sendSckt.send(pickle.dumps(pkt))
                else: print("macsend to to_" + d + " from from_" + pkt[1] + ": " + pkt[0])

        if stop:
            done = True
            break
#end BeVRVH


if len(sys.argv) != 2:
	print ("p2 <filename>\n")
	exit(1)

dev2mac = {}
dev2net = {}
dev2name = {}
mac2dev = {}
mac2ip = {}
mac2net = {}
net2mac = {}
names = []
opers = []
inFile = open(sys.argv[1])

for x in inFile:
	y = x.split()
	if len(y) == 0: continue
	try: y = y[0:y.index('#')]
	except: pass
	if len(y) == 0: continue
	if y[0] == 'vr' or y[0] == 'vs' or y[0] == 'vh': names.append(y)
	else: opers.append(y)

for n in names:
	dev2name[n[1]] = (n[0], socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM))
	if n[0] == 'vs':
		dev2net[n[1]] = n[2]
		continue
	else:
		dev2net[n[1]] = []
		dev2mac[n[1]] = []
		for i in range(2,len(n),2):
		   dev2mac[n[1]].append(n[i])
		   dev2net[n[1]].append(n[i+1].split('.')[0])
		   mac2ip[n[i]] = n[i+1]
		   mac2dev[n[i]] = n[1]
		   mac2net[n[i]] = n[i+1].split('.')[0]
		   if n[i+1].split('.')[0] not in net2mac: net2mac[n[i+1].split('.')[0]] = []
		   net2mac[n[i+1].split('.')[0]].append((n[i],socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)))

for d in dev2name:
	rc = os.fork()
	if rc == 0:
		if dev2name[d][0] == 'vs': BeVS(d, dev2mac, dev2name, dev2net, mac2dev, mac2ip, mac2net, net2mac);
		else: BeVRVH(d, dev2mac, dev2name, dev2net, mac2dev, mac2ip, mac2net, net2mac);
		exit(0)

for o in opers:
	if o[0] == 'pause':
		if o[1] == 'tty':
			while True:
				x = input("Press return to continue")
				if not x: break
		else: sleep(int(o[1]))
	elif o[0] == 'macsend':
		d = [n for n in dev2mac if o[2] in dev2mac[n]]
		sendSckt = dev2name[d[0]][1][0]
		netPkt = pickle.dumps(o)
		sendSckt.send(netPkt)
		sleep(.25)
	elif o[0] == 'prt': pass
			
for d in dev2name:
	netPkt = pickle.dumps(['STOP'])
	dev2name[d][1][0].send(netPkt)


