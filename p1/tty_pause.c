#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <fcntl.h>

main()
{
    int i, n, rc, fd, status;

    fd = open("/dev/tty", O_RDONLY);

    printf("pausing ...\n");
    i = read(fd,&n, 1);

    printf("pausing ...\n");
    i = read(fd,&n, 1);

    printf("pausing ...\n");
    i = read(fd,&n, 1);

}
