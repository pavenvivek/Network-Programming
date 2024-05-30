CC           = gcc
CFLAGS       = -O2 -std=c99
#CFLAGS       = -O0 -g

#set the following variables for custom libraries and/or other objects
EXTOBJS      =
LIBS         = -lm -lcurl
LIBPATHS     = 
INCLUDEPATHS = 

PROGRAMS     = smtp smtp-socket
all: $(PROGRAMS)

$(PROGRAMS): %: %.o
	$(CC) -o $@ $< $(LIBPATHS) $(CFLAGS) $(EXTOBJS) $(LIBS)

.c.o:
	$(CC) $(CFLAGS) $(TUNEFLAGS) $(INCLUDEPATHS) -c $<

clean:
	rm -f $(PROGRAMS) *.o *~
