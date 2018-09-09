// Name:        Ben Belden
// Class ID#:   bpb2v
// Section:     CSCI 6450-001
// Assignment:  Lab #1
// Due:         18:00:00, February 2, 2017
// Purpose:     Write a C/C++ program that implements the SLIP protocal (RFC 1055) to 
// 			    copy data from one process to a second process via a socekt pair.        
// Input:       From terminal.  
// Outut:       To terminal.
// 
 // File:        p1.c

#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include "rfc1055.c"
#define PKT_SIZE 1006

int main (int argc, char * argv[])
{
	int rc,s,r,status,sock[2];
	char writeBuf[PKT_SIZE],readBuf[PKT_SIZE];

	// open files for reading and writing
	// assume filenames are: "infile" & "outfile"
	FILE *inFile, *outFile;
	inFile = fopen("infile","r");
	outFile = fopen("outfile","w");

	socketpair(AF_UNIX,SOCK_STREAM,0,sock);
	// set fd names to make fds work in rfc1055.c
	send_sock_fd = sock[0];
	recv_sock_fd = sock[1];

	rc = fork();
	if (rc > 0) // parent - read from infile
	{
		close(recv_sock_fd);
		s=0;
		while(!feof(inFile))
		{
			s = fread(readBuf,1,PKT_SIZE,inFile);
			send_packet(readBuf,s);
		}
		close(send_sock_fd);
	}
	else // child - write to outfile
	{
		close(send_sock_fd);
		r = PKT_SIZE;
		while(r==PKT_SIZE)
		{
			r = recv_packet(writeBuf,PKT_SIZE);
			fwrite(writeBuf,1,r,outFile);
		}
		close(recv_sock_fd);
	}
	fclose(inFile);
	fclose(outFile);
	return 0;
}

