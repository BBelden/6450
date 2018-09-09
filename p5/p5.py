#!/usr/bin/env python3

## Name:        Ben Belden
## Class ID#:   bpb2v
## Section:     CSCI 6450-001
## Assignment:  Lab #5
## Due:         18:00:00,April 6,2017
## Purpose:     Add DNS,tracert,ping to project 2. 
## Input:       From preformatted file.  
## Outut:       To terminal.
## 
## File:        p5.py

import os               # fork()
import sys              # argv[]
import socket           # UNIX set()
import select           # UNIX select()
import pickle           # byte streams
from time import *      # sleep()

def beVS(d,dev2mac,dev2name,dev2net,mac2dec,mac2ip,mac2net,net2mac):
    done=False
    scktList=[]
    scktList.append(dev2name[d][1][1])
    
    for n in net2mac[dev2net[d]]: scktList.append(n[1][1])

    while not done:
        (sckt,unused,unused)=select.select(scktList,[],[],2)

        for s in sckt:
            netPkt=s.recv(256)
            pkt=pickle.loads(netPkt)
            msg=pkt[4]
            if s==dev2name[d][1][1]:
                if msg=='STOP':
                    done=True
                    break
            else:
                if pkt[2]=='2':
                    for n in net2mac[dev2net[d]]:
                        if n[0]==pkt[0]:
                            n[1][1].send(netPkt)
                            break
                elif pkt[0]=='255' or pkt[2]=='1':
                    for n in net2mac[dev2net[d]]:
                        if pkt[2]=='1':
                            pkt[0]=pkt[1]
                            netPkt=pickle.dumps(pkt)
                        n[1][1].send(netPkt)
                elif pkt[2]=='3':
                    for n in net2mac[dev2net[d]]:
                        if pkt[0] in n:
                            n[1][1].send(netPkt)
                            break
                else:
                    sent=False
                    for n in net2mac[dev2net[d]]:
                        if pkt[0] in n:
                            n[1][1].send(netPkt)
                            sent=True
                    if not sent:
                        print("[BAD SEND TO "+pkt[0]+" from switch "+d+"]")
# end beVS

def beVRVH(d,dec2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac):
    done=False
    routable=False
    destMac=None
    destNet=None
    sTime=0        
    arpCache={}    
    appMsg=[]      
    conns=[] 
    rtTbl=[]  
    scktList=[]
    scktList.append(dev2name[d][1][1])
    for n in dev2net[d]:
        for m in net2mac[n]:
            if m[0] in dev2mac[d]: scktList.append(m[1][0])
    while not done:
        (sckt,unused,unused)=select.select(scktList,[],[],0)
        if (sTime>0) and (time.time()-sTime>1) and (len(sckt)==0):
            sTime=0
            print(d+': arpreq to','unknown_Host','timed out')
            continue
        for s in sckt:
            netPkt=s.recv(256)
            pkt=pickle.loads(netPkt)
            msg=pkt[4]
            if s==dev2name[d][1][1]:
                if msg=='STOP':
                    done=True
                    break
                elif pkt[2]=='-5': rtTbl.append(msg.split())
                elif pkt[2]=='1':
                    for n in net2mac[pkt[4][0]]:
                        for myMac in dev2mac[d]:
                            if n[0]==myMac:
                                netPkt=pickle.dumps(['255',myMac,'1','4',msg])
                                n[1][0].send(netPkt)
                    sTime=time.time()

                elif pkt[2]=='3' or pkt[2]=='4' or pkt[2]=='5' or pkt[2]=='6':
                    if pkt[2]=='6':
                        if pkt[7][0]=='conn':
                            conns.append(pkt[7][1])
                            continue
                        elif pkt[7][0]=='send': 
                            connFnd=False
                            for i in range(len(conns)):
                                if pkt[6][0] in conns[i].split(':'):
                                    connFnd=True
                                    break

                            if not connFnd:
                                print(d+': failed,no connection')
                                continue

                        elif pkt[7][0]=='done':
                            for i in range(len(conns)):
                                if pkt[7][1]==conns[i]:
                                    del conns[i]
                                    break

                    mainDest=''
                    destNet=''
                    if msg.find('.') != -1:
                        destNet=msg[0]
                        for mac in mac2ip:
                            if mac2ip[mac]==msg:
                                mainDest=mac
                                break
                    else:
                        mainDest=dev2mac[msg][0]
                        destNet=mac2net[mainDest]
                    
                    pkt[5][5]=d
                    for r in rtTbl:
                        if r[0].find('.') != -1: r[0]=r[0][0]
                        if r[0]==destNet:
                            pkt[1]=r[1]
                            if len(r)==3:
                                for mac in mac2ip:
                                    if mac2ip[mac]==r[2]:
                                        pkt[0]=mac
                                        break
                            else:
                                rtrFnd=False
                                for dev in dev2mac:
                                    if len(dev2mac[dev])>1:
                                        for rMac in dev2mac[dev]:
                                            if mac2net[rMac]==mac2net[pkt[1]]:
                                                rtrFnd=True
                                                pkt[0]=rMac
                                                break
                                        if rtrFnd: break
                            break
                        elif r[0]=='def':
                            pkt[1]=r[1]
                            for mac in mac2ip:
                                if mac2ip[mac]==r[2]:
                                    pkt[0]=mac
                                    break
                            break
                    for n in net2mac[mac2net[pkt[1]]]:
                        if n[0]==pkt[1]:
                            pkt[5][1] -= 1
                            netPkt=pickle.dumps(pkt)
                            n[1][0].send(netPkt)
                            break
                    if pkt[2]=='3': print(d+': sent ping to',pkt[4])
                    elif pkt[2]=='4': print(d+': sent traceroute to',pkt[4])
                elif msg=='ARPPRT':
                    if len(arpCache)>0:
                        for ipAddr in arpCache:
                            print(d+':',ipAddr,arpCache[ipAddr],mac2net[arpCache[ipAddr]])
                    else: print(d+'\'s','arp cache empty')
                else:
                    toHost=''
                    if pkt[0]=='255': toHost='everyone'
                    else: toHost=mac2dev[pkt[0]]
                    print(d+':  macsend to '+toHost+' on '+pkt[1]+': '+msg)
                    switchNum=mac2net[pkt[1]]
                    macSockList=net2mac[switchNum]  
                    for n in macSockList:
                        if pkt[1]==n[0]:
                            n[1][0].send(netPkt)
                            break
            else:
                if pkt[2]=='1':
                    onMac=None
                    for mac in dev2mac[d]:
                        if mac2net[mac]==mac2net[pkt[1]]: onMac=mac
                    if mac2ip[onMac]==pkt[4]:
                        print(d+':','arpreq from',mac2dev[pkt[1]],'on',onMac+':',pkt[4])
                        pkt[1]=onMac
                        pkt[2]='2'
                        pkt[4]+=','+onMac
                        netPkt=pickle.dumps(pkt)
                        s.send(netPkt)
                        print(d,'arpreply to',mac2dev[pkt[0]],'on',onMac+':',pkt[4])
                elif pkt[2]=='2':
                    sTime=0
                    onMac=None
                    for mac in dev2mac[d]:
                        if mac2net[mac]==mac2net[pkt[1]]: onMac=mac
                    print(d+':','arpreply from',mac2dev[pkt[1]],'on',onMac+':',pkt[4])
                    ipMac=pkt[4].split(',')
                    arpCache[ipMac[0]]=ipMac[1]
                elif pkt[2]=='3' or pkt[2]=='4' or pkt[2]=='5' or pkt[2]=='6':
                    if pkt[5][1]==0:
                        print(d+': TTL at 0')
                        continue

                    if pkt[2]=='4': pkt[5][5]=pkt[5][5]+' '+d

                    if pkt[4].find('.') != -1:
                        for mac in mac2ip:
                            if mac2ip[mac]==pkt[4]:
                                destMac=mac
                                destNet=mac2net[mac]
                                break
                    else:
                        destMac=dev2mac[pkt[4]][0]
                        destNet=mac2net[destMac]

                    if destMac in dev2mac[d]:
                        if pkt[2]=='3':
                            print(d+': received ping from',pkt[5][5].split()[0])
                            continue
                        elif pkt[2]=='4':
                            print(d+': received traceroute from', pkt[4]+'; route:',pkt[5][5])
                            continue
                        elif pkt[2]=='5':
                            print(d,'received tcptest from',pkt[5][5].split()[0],'for port',pkt[6][0],pkt[6][1])
                            continue
                        elif pkt[2]=='6':
                            if pkt[7][0]=='send':
                                portFnd=False
                                for i in range(len(appMsg)):
                                    if pkt[6][0] in appMsg[i]:
                                        portFnd=True
                                        appMsg[i][1]+='\n'+pkt[7][2]
                                        print(d,'received',pkt[7][2])
                                        break
                                if not portFnd:
                                    print(d,'received',pkt[7][2])
                                    appMsg.append([pkt[6][0],pkt[7][2]])
                                continue
                            elif pkt[7][0]=='done':
                                for i in range(len(conns)):
                                    if pkt[7][1]==conns[i]:
                                        del conns[i]
                                        break

                                for i in range(len(appMsg)):
                                    if pkt[6][0] in appMsg[i]:
                                        print(d,'printing message below\n'+appMsg[i][1])
                                        print()
                                        del appMsg[i]
                                        break
                                continue

                    else:
                        for r in rtTbl:
                            if r[0]==destNet:
                                pkt[1]=r[1]
                                if len(r)==3:
                                    for mac in mac2ip:
                                        if mac2ip[mac]==r[2]:
                                            routable=True
                                            pkt[0]=mac
                                            break

                                else:
                                    if destNet==mac2net[r[1]]:
                                        routable=True
                                        pkt[0]=destMac
                                    else:
                                        rtrFnd=False
                                        for dev in dev2mac:
                                            if len(dev2mac[dev])>1:
                                                for rMac in dev2mac[dev]:
                                                    if mac2net[rMac]==mac2net[pkt[1]]:
                                                        rtrFnd=True
                                                        routable=True
                                                        pkt[0]=rMac
                                                        break
                                                if rtrFnd: break
                                break
                            
                            elif r[0]=='def':
                                pkt[1]=r[1]
                                for m in mac2ip:
                                    if mac2ip[m]==r[2]:
                                        routable=True
                                        pkt[0]=m
                                        break
                                break

                        if not routable:
                            print(d+':  **** no route to host:',pkt[4])
                            continue
                        pkt[5][1] -= 1
                        netPkt=pickle.dumps(pkt)
                        for n in net2mac[mac2net[pkt[1]]]:
                            if pkt[1]==n[0]:
                                n[1][0].send(netPkt)
                                break

                elif pkt[0] in dev2mac[d] or pkt[0]=='255':
                    onMac=''
                    for m in dev2mac[d]:
                        if mac2net[m]==mac2net[pkt[1]]:
                            onMac=m
                            break
                    print(d+':  macsend from '+mac2dev[pkt[1]]+' on '+onMac+': '+msg)
# end beVRVH


if len(sys.argv) != 2:
	print('p5 <filename>\n')
	exit(1)

dev2name={}
dev2mac={}
dev2net={}
mac2ip={}
mac2net={}
mac2dev={}
net2mac={} 
names=[]
opers=[]

inFile=open(sys.argv[1])

for x in inFile:
	y=x.split()
	if len(y)==0: continue
	if y[0].startswith('#'): continue
	z=0
	for t in y:
		if t.startswith('#'): break
		z+=1
	y=y[0:z]    
	if y[0]=='vs' or y[0]=='vr' or y[0]=='vh': names.append(y)
	else: opers.append(y)

for n in names:
	dev2name[n[1]]=(n[0],socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM))
	if n[0]=='vs':
		dev2net[n[1]]=n[2]
	else:
		dev2mac[n[1]]=[]
		dev2net[n[1]]=[]
		for i in range(2,len(n),2):
			dev2mac[n[1]].append(n[i])
			dev2net[n[1]].append(n[i+1].split('.')[0])
			mac2dev[n[i]]=n[1]
			mac2ip[n[i]]=n[i+1]
			mac2net[n[i]]=n[i+1].split('.')[0]
			if n[i+1].split('.')[0] not in net2mac:	net2mac[n[i+1].split('.')[0]]=[]
			net2mac[n[i+1].split('.')[0]].append((n[i],socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)))

rcList=[]
for d in dev2name:
	rc=os.fork()
	rcList.append(rc)
	if rc==0:
		if dev2name[d][0]=='vs': beVS(d,dev2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac)
		else: beVRVH(d,dev2mac,dev2name,dev2net,mac2dev,mac2ip,mac2net,net2mac)
		exit(0)

for o in opers:
	if o[0]=='prt':
		if len(o)==1: print()
		else: print(" ".join(o[1:]))
	elif o[0]=='pause':
		if o[1]=='tty':
			while True:
				x=input('\"press return to continue\"\n')
				if not x: break
		else: sleep(int(o[1]))
	elif o[0]=='macsend':
		netPkt=pickle.dumps([o[3],o[2],str(0),str(len(o[1])+4),o[1]])
		sendSckt=dev2name[mac2dev[o[2]]]
		sendSckt[1][0].send(netPkt)
	elif o[0]=='arptest':
		netPkt=pickle.dumps([o[1],'0','1','4',o[2]])
		sendSckt=dev2name[o[1]] 
		sendSckt[1][0].send(netPkt)
	elif o[0]=='arpprt':
		netPkt=pickle.dumps(['0','0','0','4','ARPPRT'])
		sendSckt=dev2name[o[1]]
		sendSckt[1][0].send(netPkt)
		sleep(.1)
	elif o[0]=='route':
		pkt=''
		for i in range(2,len(o)): pkt+=o[i]+' '
		pkt=pkt.rstrip(' ')
		netPkt=pickle.dumps(['0','0','-5','4',pkt])
		sendSckt=dev2name[o[1]] 
		sendSckt[1][0].send(netPkt)
		sleep(.1)
	elif o[0]=='iptest':
		ipPkt=['7',6,'0','0','0','0']
		netPkt=pickle.dumps(['0','0','3','4',o[2],ipPkt])
		sendSckt=dev2name[o[1]] 
		sendSckt[1][0].send(netPkt)
	elif o[0]=='trtest':
		ipPkt=['7',6,'0','0','0','0']
		netPkt=pickle.dumps(['0','0','4','4',o[2],ipPkt])
		sendSckt=dev2name[o[1]] 
		sendSckt[1][0].send(netPkt)
	elif o[0]=='tcptest':
		ipPkt=['7',6,'0','0','0','0']
		tcpPkt=[o[3],o[4]]
		netPkt=pickle.dumps([o[2],o[1],'5','4',o[2],ipPkt,tcpPkt])
		sendSckt=dev2name[o[1]]
		sendSckt[1][0].send(netPkt)
	elif o[0]=='ftpd_conn':
		ipPkt=['7',6,'0','0','0','0']
		tcpPkt=[o[3],None]
		appPkt=['conn',o[1]+':'+o[2]+':'+o[3],None]
		netPkt=pickle.dumps(['0','0','6','4',o[2],ipPkt,tcpPkt,appPkt])
		sendSckt=dev2name[o[1]]
		sendSckt[1][0].send(netPkt)
	elif o[0]=='ftp_send':
		ipPkt=['7',6,'0','0','0','0']
		tcpPkt=[o[3],o[4]]
		appPkt=['send',o[1]+':'+o[2]+':'+o[3],o[4]]
		netPkt=pickle.dumps(['0','0','6','4',o[2],ipPkt,tcpPkt,appPkt])
		sendSckt=dev2name[o[1]]
		sendSckt[1][0].send(netPkt)
	elif o[0]=='ftp_done':
		ipPkt=['7',6,'0','0','0','0']
		tcpPkt=[o[3],None]
		appPkt=['done',o[1]+':'+o[2]+':'+o[3],None]
		netPkt=pickle.dumps(['0','0','6','4',o[2],ipPkt,tcpPkt,appPkt])
		sendSckt=dev2name[o[1]] 
		sendSckt[1][0].send(netPkt)

for dev in dev2name:
	dev2name[dev][1][0].send(pickle.dumps( ['0','0','0','8','STOP'] ))
for rc in rcList:
	os.waitpid(rc,0)

