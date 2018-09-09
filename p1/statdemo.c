#include <stdio.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    int fd;
    struct stat sb;

    if ((fd = open(argv[1], O_RDONLY)) < 0) {
        perror("open");
        return 1;
    }
    
    if (fstat(fd, &sb)) {
        perror("fstat");
        return 1;
    }

    printf("size of file %s is %d\n",argv[1], sb.st_size);

    return 0;
}
