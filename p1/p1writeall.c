#include <stdio.h>

int main(int argc, char *argv[])
{
    int i;
    unsigned char c;

    for (i=0; i < 256; i++)
    {
        c = i;
        write(1,&c,1);
    }
}
