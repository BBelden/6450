#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>

main()
{
    int rc, status, sock[2];
    char buf[1000];

    socketpair(AF_UNIX,SOCK_STREAM,0,sock);
    printf("fds = %d %d\n",sock[0],sock[1]);

    rc = fork();
    printf("rc=%d\n",rc);
    if (rc > 0)
    {
        close(sock[1]);   // unused by this proc
	write(sock[0],"hello",6);
	read(sock[0],buf,6);
	printf("%d: recvd %s\n",getpid(),buf);
	rc = wait(&status);
        close(sock[0]);
    }
    else
    {
        close(sock[0]);  // unused by this proc
	read(sock[1],buf,6);
	printf("%d: recvd %s\n",getpid(),buf);
        write(sock[1],"howdy",6);
        close(sock[1]);
    }
}
