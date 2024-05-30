#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>

#include "a2.h"
#include "a3.h"
#include "a4.h"

#define DEFAULT_PORT 12345

typedef struct cfg {
  long  port;
  char *iface;
  char *server;
  FILE *fstream;
  int   use_udp;
  int   use_rudp;
} cfg_t;

/*
 * If we are a server, launch the appropriate methods to handle server
 * functionality based on the configuration arguments.
 */
void run_server(cfg_t *cfg) {
  printf("Hello, I am a server\n");
  /* For example, if cfg->udp is true, then call the server UDP handler */
}

/*
 * If we are a client, launch the appropriate methods to handle client
 * functionality based on the configuration arguments.
 */
void run_client(cfg_t *cfg) {
  printf("Hello, I am a client\n");
  /* For example, if cfg->udp is true, then call the client UDP handler */
}

void usage(const char *argv0) {
  printf("Usage:\n");
  printf("  %s            start a server and wait for connection\n", argv0);
  printf("  %s <host>     connect to server at <host>\n", argv0);
  printf("\n");
  printf("Options:\n");
  printf("  -p, --port=<port>      listen on/connect to port <port>\n");
  printf("  -i, --iface=<dev>      listen on interface <dev>\n");
  printf("  -f, --file=<filename>  file to read/write\n");
  printf("  -u, --udp              use UDP (default TCP)\n");
  printf("  -r, --rudp             use RUDP (1=stopwait, 2=gobackN)\n");
}

int main(int argc, char **argv) {
  int c;
  char *fname = NULL;
  
  /* The configuration structure for netster */
  cfg_t cfg = {
    .port = DEFAULT_PORT,  /* which port to use */
    .iface = NULL,         /* which interface to use */
    .server = NULL,        /* the server to connect to */
    .fstream = NULL,       /* the open file stream if fname given */
    .use_udp = 0,          /* should we use UDP (default TCP) */
    .use_rudp = 0,         /* should we use RUDP (default TCP) */
  };
  
  static struct option long_options[] = {
    { .name = "file",           .has_arg = 1, .val = 'f' },
    { .name = "iface",          .has_arg = 1, .val = 'i' },
    { .name = "port",           .has_arg = 1, .val = 'p' },
    { .name = "rudp",           .has_arg = 1, .val = 'r' },
    { .name = "udp",            .has_arg = 0, .val = 'u' },
    { 0 }
  };

  while (1) {
    c = getopt_long(argc, argv, "f:i:p:r:u", long_options, NULL);
    if (c == -1)
      break;
    
    switch (c) {
    case 'p':
      cfg.port = strtol(optarg, NULL, 0);
      if (cfg.port < 0 || cfg.port > 65535) {
        usage(argv[0]);
        return 1;
      }
      break;
      
    case 'i':
      cfg.iface = strdup(optarg);
      break;
      
    case 'u':
      cfg.use_udp = 1;
      break;
      
    case 'r':
      cfg.use_rudp = atoi(optarg);
      break;

    case 'f':
      fname = strdup(optarg);
      break;
      
    default:
      usage(argv[0]);
      return 1;
      break;
    }
  }
  
  if (optind == argc - 1)
    cfg.server = strdup(argv[optind]);

  /* open the file if specified */
  if (fname) {
    const char *mode = (cfg.server) ? "r" : "w+";
    cfg.fstream = fopen(fname, mode);
    if (!cfg.fstream) {
      perror("fopen: ");
      exit(1);
    }
  }
  
  /* Here we decide if we started as a server or client! */
  if (cfg.server)
    run_client(&cfg);
  else
    run_server(&cfg);

  if (fname && cfg.fstream) {
    fclose(cfg.fstream);
  }
  
  return 0;
}
