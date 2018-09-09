#!/usr/bin/env python3

## Name:        Ben Belden
## Class ID#:   bpb2v
## Section:     CSCI 6450-001
## Assignment:  Lab #4
## Due:         18:00:00,April 6,2017
## Purpose:     Add DNS,tracert,ping to project 2. 
## Input:       From preformatted file.  
## Outut:       To terminal.
## 
## File:        p4.py

import os               # fork()
import sys              # argv[]
import socket           # UNIX socket()
import select           # UNIX select()
import pickle           # byte streams
from time import *      # sleep()

def BeVS(d,dev2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac):
    done=False
    stop=False
    sendSckt=None
    scktList=[]
    for n in net2mac[dev2net[d]]:  scktList.append(n[1][1]) # select list
    scktList.append(dev2name[d][1][1]) # sckt to interp
    
    while not done:
        (sckt,unused,unused)=select.select(scktList,[],[],3)
        for s in sckt:
            pkt=pickle.loads(s.recv(255))
            if(pkt[0]=='STOP'):  stop=True
            elif(pkt[2]==1): # arp req rcvd
                for x in net2mac[dev2net[d]]: # bcast to all hosts
                    for num in dev2net[pkt[4][0].split('.')[0]]:
                        if dev2net[d]==num:  x[1][1].send(pickle.dumps(pkt))
            elif(pkt[2]==2): # arp reply rcvd
                # handle pkt and send to VR/VS 
                sendSckt=None 
                for x in net2mac[dev2net[d]]:
                    if sendSckt==None:
                        for mac in dev2mac[pkt[0]]:
                            if mac==x[0]: 
                                sendSckt=x[1][1]
                                break
                    else:  break
                if sendSckt != None:  sendSckt.send(pickle.dumps(pkt))
            else: # macsend
                # handle pkt and send to VR/VS 
                sendSckt=None 
                for n in net2mac:
                    if sendSckt==None:
                        for m in net2mac[n]:
                            if pkt[0]==m[0]: 
                                sendSckt=m[1][1]
                                break
                if pkt[0]=='255': # pkt is bcast
                    for x in net2mac[dev2net[d]]:  x[1][1].send(pickle.dumps(pkt))
                elif dev2net[d] != mac2ip[pkt[0]].split('.')[0]: # host not on net
                    print("[BAD SEND TO "+pkt[0]+" from switch "+d+"]")
                    continue
                else: # on same net  
                    if mac2ip[pkt[1]].split('.')[0]==mac2ip[pkt[0]].split('.')[0]:
                        sendSckt.send(pickle.dumps(pkt))
        if stop:
            done=True
            break
# end BeVS

def BeVRVH(d,dev2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac,arpcache,rtTable):
    done=False
    stop=False
    dest=None
    mac=None
    net=None
    sendSckt=None
    sTime=0
    scktList=[]
    scktList.append(dev2name[d][1][1]) # sckt to interp 
    for n in dev2name: # setup select list
        if dev2name[n][0]=='vs':
            for m in net2mac[dev2net[n]]:
                if m[0] in dev2mac[d]:  scktList.append(m[1][0])
    while not done:
        (sckt,unused,unused)=select.select(scktList,[],[],0)
        if sTime>0 and time()-sTime>1 and len(sckt)==0:
            sTime=0
            print(d+': arpreq','to unknown Hostname time out')
            continue
        for s in sckt:
            pkt=pickle.loads(s.recv(255))
            if(pkt[0]=='STOP'):  stop=True
            elif len(pkt)>2 and pkt[2]==1: # arp req pkt rcvd
                for item in dev2mac[d]:
                    if mac2ip[item]==pkt[4][1]: # arp req for this host,send reply
                        sendSckt=None 
                        for i in net2mac: # get sckt to send pkt to
                            if sendSckt==None:
                                for x in net2mac[i]:
                                    if dev2mac[pkt[4][0]][0]==x[0]: 
                                        sendSckt=x[1][0]
                                        break
                        if sendSckt != None: # sckt found,send stuff
                            arp_reply=[pkt[4][0],dev2mac[d],2,0,[pkt[4],dev2mac[d]]]
                            arp_reply[3]=sys.getsizeof(arp_reply)
                            sendSckt.send(pickle.dumps(arp_reply))

            elif len(pkt)>2 and pkt[2]==2: # recvd arp reply
                sTime=0
                print(mac2dev[pkt[1][0]]+": arpreply to "+str(pkt[0])+" on "+str(dev2mac[d])+": "+str([str(pkt[4][0][1]),pkt[4][1][0]]))
                arpcache[pkt[4][0][1]]=pkt[4][1][0]
            elif pkt[2]==3 or pkt[2]==4: # iptest
                if pkt[2]==4:  pkt[4][4].append(d)
                if pkt[2]==4 and pkt[4][1]==d:
                    print(d+': received traceroute from '+pkt[4][0]+'; route: \n\t'+str(pkt[4][4]))
                elif pkt[2]==3 and pkt[4][1]==d:  print(d+': received ping from '+pkt[4][0])
                elif pkt[2]==3 and pkt[4][1] in mac2ip[dev2mac[d][0]]:
                    print(d+': received ping from '+pkt[4][0])
                else:
                    if pkt[4][1].find('.') >= 0:  net=pkt[4][1].split('.')[0]
                    else:  net=dev2net[pkt[4][1]][0]
                    for route in rtTable[d]:
                        if route[0]==net:
                            mac=route[1]
                            if len(route) > 2:
                                for m in mac2ip:
                                    if mac2ip[m]==route[2]:
                                        dest=m
                                        break
                            else:
                                if pkt[4][1].find('.') >= 0:
                                    for m in mac2ip:
                                        if mac2ip[m]==pkt[4][1]:
                                            dest=m
                                            break
                                else:  dest=dev2mac[pkt[4][1]][0]
                            break
                        elif route[0]=='def':
                            mac=route[1]
                            for m in mac2ip:
                                if mac2ip[m]==route[2]:  dest=m
                    if mac==None:
                        print(d+': **** no route to host: '+pkt[4][1])
                        break
                    sendSckt=None
                    for i in net2mac:
                        if sendSckt==None:
                            for x in net2mac[i]:
                                if x[0]==mac:
                                    sendSckt=x[1][0]
                                    break
                    if sendSckt != None:
                        ip_pkt=[pkt[4][0],pkt[4][1],0,0,pkt[4][4]]
                        mac_pkt=[dest,mac,pkt[2],0,ip_pkt]
                        sendSckt.send(pickle.dumps(mac_pkt))

            else: # macsend
                if pkt[0]=='macsend':
                    if pkt[3]=='255':  to_hostname='255'
                    else:  to_hostname=mac2dev[pkt[3]]
                    print(d+": macsend to "+str(to_hostname)+" on "+pkt[2]+": "+pkt[1])
                    net_to_send=mac2ip[pkt[2]].split('.')[0] 
                    sendSckt=None 
                    for i in net2mac: # get sckt
                        if sendSckt==None:
                            for x in net2mac[i]:
                                if pkt[2]==x[0]: 
                                    sendSckt=x[1][0]
                                    break
                    if sendSckt != None: # send stuff if found sckt
                        mac_pkt=[pkt[3],pkt[2],0,0,pkt[1]]
                        mac_pkt[3]=sys.getsizeof(mac_pkt)
                        sendSckt.send(pickle.dumps(mac_pkt))
                elif pkt[0]=='arptest': # send arp req to VS
                    sendSckt=None
                    for i in net2mac: # get sckt
                        if sendSckt==None:
                            for x in net2mac[i]:
                                for mac in dev2mac[pkt[1]]:
                                    if mac2ip[mac].split('.')[0]==pkt[2].split('.')[0] and mac==x[0]: 
                                        sendSckt=x[1][0]
                                        break
                    if sendSckt != None: # send stuff if found sckt
                        print(d+": arpreq to 255 on "+str(dev2mac[d])+": "+pkt[2])
                        arp_pkt=['255',pkt[1],1,0,[pkt[1],pkt[2]]]
                        arp_pkt[3]=sys.getsizeof(arp_pkt)
                        sendSckt.send(pickle.dumps(arp_pkt))
                    sTime=time()

                elif pkt[0]=='arpprt':  print('[ARP Cache for '+d+']: '+str(arpcache))
                elif pkt[0]=='iptest' or pkt[0]=='trtest':
                    if pkt[0]=='iptest':  print(d+': sent ping to '+pkt[2])
                    elif pkt[0]=='trtest':  print(d+': sent traceroute to '+pkt[2])
                    if pkt[2].find('.') >= 0:  net=pkt[2].split('.')[0]
                    else:  net=(mac2ip[dev2mac[pkt[2]][0]]).split('.')[0]
                    for route in rtTable[d]:
                        if route[0]==net:
                            mac=route[1]
                            if len(route) > 2:
                                for m in mac2ip:
                                    if mac2ip[m]==route[2]:
                                        dest=m
                                        break
                            else:
                                if pkt[2].find('.') >= 0:
                                    for m in mac2ip:
                                        if mac2ip[m]==pkt[2]:
                                            dest=m
                                            break
                                else:  dest=dev2mac[pkt[2]][0]
                            break
                        elif route[0]=='def':
                            mac=route[1]
                            for m in mac2ip:
                                if mac2ip[m]==route[2]:
                                    dest=m
                                    break
                    if mac==None:  print(d+': **** no route to host: '+pkt[2])
                    sendSckt=None
                    for i in net2mac:
                        if sendSckt==None:
                            for x in net2mac[i]:
                                if x[0]==mac:
                                    sendSckt=x[1][0]
                                    break

                    if sendSckt != None:
                        ip_pkt=[pkt[1],pkt[2],0,0,[]]
                        code=3
                        if pkt[0]=='trtest':
                            code=4
                            ip_pkt[4].append(d)
                        mac_pkt=[dest,dev2mac[pkt[1]][0],code,0,ip_pkt]
                        sendSckt.send(pickle.dumps(mac_pkt))

                else: # only when VR/VS recvs from other VR/VS,not interp
                    if pkt[0]=='255':  from_hostname=mac2dev[pkt[1]]  # bcast msg
                    else:  from_hostname=mac2dev[pkt[0]] # msg to this host
                    print(d+": macsend from "+str(from_hostname)+" on "+str(pkt[1])+": "+pkt[4])
        if stop:
            done=True
            break
# end BeVRVH

	

if len(sys.argv) != 2:
	print ("p4 <filename>\n")
	exit(1)

arpcache={} 
dev2mac={}
dev2name={}
dev2net={}
mac2dev={}
mac2ip={}
mac2net={}
net2mac={}
rtTable={}
names=[]
opers=[]
inFile=open(sys.argv[1])

for x in inFile:
	y=x.split()
	if len(y)==0:  continue
	try:  y=y[0:y.index('#')]
	except:  pass
	if len(y)==0:  continue
	if y[0]=='vr' or y[0]=='vs' or y[0]=='vh' or y[0]=='route':  names.append(y)
	else:  opers.append(y)


for n in names:
	dev2name[n[1]]=(n[0],socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM))
	if n[0]=='vs':
		dev2net[n[1]]=n[2]
		continue
	elif n[0]=='route':
		if n[1] not in rtTable:  rtTable[n[1]]=[]
		rtTable[n[1]].append(n[2:])
	else:
		dev2net[n[1]]=[]
		dev2mac[n[1]]=[]
		for i in range(2,len(n),2):
		   dev2mac[n[1]].append(n[i])
		   dev2net[n[1]].append(n[i+1].split('.')[0])
		   mac2dev[n[i]]=n[1]
		   mac2ip[n[i]]=n[i+1]
		   mac2net[n[i]]=n[i+1].split('.')[0]
		   if n[i+1].split('.')[0] not in net2mac:  net2mac[n[i+1].split('.')[0]]=[]
		   net2mac[n[i+1].split('.')[0]].append((n[i],socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)))

# create all processes
for d in dev2name:
	rc=os.fork()
	if rc==0: # child
		if dev2name[d][0]=='vs':  BeVS(d,dev2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac);
		else:  BeVRVH(d,dev2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac,arpcache,rtTable);
		exit(0)

for o in opers:
	if o[0]=='pause':
		if o[1]=='tty':
			while True:
				x=input("Press return to continue")
				if not x:  break
		else:  sleep(int(o[1]))
	elif o[0]=='macsend':
		d=[n for n in dev2mac if o[2] in dev2mac[n]]
		sendSckt=dev2name[d[0]][1][0]
		netPkt=pickle.dumps(o)
		sendSckt.send(netPkt)
		sleep(.25)
	elif o[0]=='prt':
		if len(o)==1:  print()
		else:
			str=''
			for word in o[1:]:
				if word[0]=='#':  break
				str += word+' '
			print(str[:-1])
	elif o[0]=='arptest':
		sendSckt=dev2name[o[1]][1][0]
		netPkt=pickle.dumps(o)
		sendSckt.send(netPkt)
		sleep(.1)
	elif o[0]=='arpprt':
		sendSckt=dev2name[o[1]][1][0]
		netPkt=pickle.dumps(o)
		sendSckt.send(netPkt)
		sleep(.1)
	elif o[0]=='iptest':
		sendSckt=dev2name[o[1]][1][0]
		netPkt=pickle.dumps(o)
		sendSckt.send(netPkt)
		sleep(.1)
	elif o[0]=='trtest':
		sendSckt=dev2name[o[1]][1][0]
		netPkt=pickle.dumps(o)
		sendSckt.send(netPkt)
		sleep(.1)

# shutdown all devices
for d in dev2name:
	sleep(.01)
	netPkt=pickle.dumps(['STOP'])
	dev2name[d][1][0].send(netPkt)

