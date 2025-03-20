CC = gcc
CFLAGS = -g
LIBDIR = /usr/lib

all: libgpxbaikal.c
	$(CC) $(CFLAGS) libgpxbaikal.c -shared -fPIC -o libgpxbaikal.so -lm

install: libgpxbaikal.so
	install -v -o root -g root -m 644 libgpxbaikal.so $(LIBDIR)
	rm libgpxbaikal.so

prog: $(PROG).c
	$(CC) $(CFLAGS) $(PROG).c -o $(PROG) -lgpxbaikal


