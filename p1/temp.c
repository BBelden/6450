#include <stdio.h>

int main(int argc, char *argv[])
{
    unsigned char c;

    c = 0300;

    printf(":%c:  :%d:  :%02x:", c,c,c);
}
