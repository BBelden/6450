#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <errno.h>

#define NUMFORKS 4

void main(int argc, char *argv[])
{
    int i, n, rc, numdone, doneflag[NUMFORKS],  sockpairs[8][2];
    char buf[1000];
    fd_set readfds;
    struct timeval tv;

    for (i=0; i < NUMFORKS; i ++)
    {
        doneflag[i] = 0;
        socketpair(AF_UNIX,SOCK_STREAM,0,sockpairs[i]);
        printf("loop %d  fds %d %d\n",i,sockpairs[i][0],sockpairs[i][1]);
        rc = fork();
        if (rc == 0)  // child
        {
            close(sockpairs[i][0]);  // unused by child
            read(sockpairs[i][1],buf,6);
            printf("child %d: recvd %s\n",i,buf);
            sprintf(buf,"howdy from child %d",i);
            write(sockpairs[i][1],buf,20);
            close(sockpairs[i][1]);
            exit(0);
        }
        else
        {
            close(sockpairs[i][1]);   // unused by parent
            write(sockpairs[i][0],"hello",6);
        }
    }

    // parent only here
    numdone = 0;
    while (numdone < NUMFORKS)
    {
        FD_ZERO( &readfds );
        for (i=0; i < NUMFORKS; i++)
        {
            if ( ! doneflag[i])
                FD_SET( sockpairs[i][0], &readfds );
        }
        tv.tv_sec = 5;
        tv.tv_usec = 0;

        rc = select( FD_SETSIZE, &readfds, NULL, NULL, &tv );

        if (rc == 0)
	{
            printf("select timed out\n");
            continue;
        } 
        if (rc == -1  &&  errno == EINTR)
	{
            printf("select interrupted; continuing\n");
            continue;
        }
        if ( rc < 0 )
	{
            perror("select failed");
            break;
        }

        for (i=0; i < NUMFORKS; i++)
        {
            if (FD_ISSET(sockpairs[i][0],&readfds))
            {
                n = read(sockpairs[i][0],buf,100);
                if (n == -1)
                {
                    perror("read failed\n");
                    break;
                }
                else if (n == 0)
                {
                    numdone += 1;
                    doneflag[i] = 1;
                    close(sockpairs[i][0]);
                }
                else
                {
                    printf("parent :%s:\n",buf);
                }
            }
        }
    }

}
