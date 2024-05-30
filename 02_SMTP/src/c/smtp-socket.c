#define _POSIX_C_SOURCE 200112L
#define BUF_SIZE 255
#define SUCCESS 0
#define FAILURE -1

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main(int argc, char *argv[])
{
   struct sockaddr_in *sin;
   struct addrinfo hints;
   struct addrinfo *res, *res_i;
   int sock_d, addr_i;
   ssize_t nread;
   char buf[BUF_SIZE] = {'\0'};

   if (argc < 3) 
   {
      fprintf(stderr, "Usage: %s host port \n", argv[0]);
      return FAILURE;
   }

   memset(&hints, 0, sizeof(struct addrinfo));
   /*Initializing hints*/
   hints.ai_family = AF_UNSPEC;
   hints.ai_socktype = SOCK_STREAM;
   hints.ai_protocol = 0;

   addr_i = getaddrinfo(argv[1], argv[2], &hints, &res);
   if (addr_i != 0) 
   {
      fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(addr_i));
      return FAILURE;
   }


   for (res_i = res; res_i != NULL; res_i = res_i->ai_next) 
   {
      sock_d = socket(res_i->ai_family, res_i->ai_socktype, res_i->ai_protocol);
      
      /*check if socket creation is successfull*/
      if (sock_d == -1)
      {
         continue;
      }

      /*check if connection is successfull*/
      if (connect(sock_d, res_i->ai_addr, res_i->ai_addrlen) != -1)
      {
         sin = (struct sockaddr_in *) res_i->ai_addr;
         printf("IP address of server %s: %s\n", argv[1], inet_ntoa(sin->sin_addr));
         break;
      }

      close(sock_d);
   }

   if (res == NULL) 
   {
      fprintf(stderr, "Could not connect\n");
      return FAILURE;
   }
   else 
   {
     printf("Connected successfully to %s !\n", argv[1]);
   }

   freeaddrinfo(res);

   nread = read(sock_d, buf, BUF_SIZE);
   if (nread == -1) 
   {
      perror("read");
      return FAILURE;
   }

   printf("Welcome message : %s", buf);
   close(sock_d);

   return SUCCESS;
}
