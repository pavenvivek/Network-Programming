#define _POSIX_C_SOURCE 200809L
#define SUCCESS 0
#define FAILURE -1

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>

typedef struct cfg {
  char *server;
  char *from_address;
  char *to_address;
  char *message;
} cfg_t;


struct data_source {
  const char *ptr;
  size_t ln;
};
 

static size_t read_callback(void *dest, size_t size, size_t nmemb, void *userdata)
{
  struct data_source *data_src = (struct data_source *) userdata;
  size_t buffer_size = size * nmemb;
 
  if (data_src->ln) 
  {
     size_t payload_len = data_src->ln;
     /*check if payload length is greater than the allowed message length*/
     if (payload_len > buffer_size)
     {
        payload_len = buffer_size;
     }
    
     memcpy(dest, data_src->ptr, payload_len);
 
     data_src->ptr = data_src->ptr + payload_len;
     data_src->ln = data_src->ln - payload_len;
    
     return payload_len; 
  }
 
  return 0;
}


int send_mail(cfg_t *cfg) 
{
  printf("Arguments: %s %s %s %s\n", cfg->server,
	 cfg->from_address, cfg->to_address, cfg->message);
	 
  CURL *curl;
  CURLcode res;
  struct curl_slist *recv_ls = NULL;
  struct data_source data_src;
  char msg[200] = {'\0'};
  
  /*Message creation*/
  strcpy(msg, "To: ");
  strcat(msg, cfg->to_address);
  strcat(msg, "\r\n");
  strcat(msg, cfg->message);

  data_src.ptr = msg;
  data_src.ln = strlen(msg);
  
  curl = curl_easy_init();
  if(curl) 
  {
     curl_easy_setopt(curl, CURLOPT_URL, cfg->server);
     curl_easy_setopt(curl, CURLOPT_MAIL_FROM, cfg->from_address);

     recv_ls = curl_slist_append(recv_ls, cfg->to_address);
     curl_easy_setopt(curl, CURLOPT_MAIL_RCPT, recv_ls);
     curl_easy_setopt(curl, CURLOPT_READFUNCTION, read_callback);
     curl_easy_setopt(curl, CURLOPT_READDATA, &data_src);
     curl_easy_setopt(curl, CURLOPT_UPLOAD, 1L);
 
     res = curl_easy_perform(curl);
 
     if(res != CURLE_OK)
     {
        fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        return FAILURE;
     }
 
     curl_slist_free_all(recv_ls);
     curl_easy_cleanup(curl);
  }

  return SUCCESS;
}

int main(int argc, char **argv) {
  cfg_t cfg;
  int rs = -1;  

  if (argc < 5) {
    /*run as ./smtp smtp://mail-relay.iu.edu <from_addr> <to_addr> <msg>*/
    fprintf(stderr,
	    "Usage: %s <server> <from> <to> <message>\n",
	    argv[0]);
    exit(1);
  }

  cfg.server = strdup(argv[1]);
  cfg.from_address = strdup(argv[2]);
  cfg.to_address = strdup(argv[3]);
  cfg.message = strdup(argv[4]);
  
  rs = send_mail(&cfg);

  if (rs == SUCCESS)
  {
     printf ("Message send to %s for delivery !\n", argv[1]);
  }

  return 0;
}
