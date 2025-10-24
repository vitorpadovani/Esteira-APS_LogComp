CC      = gcc
LEX     = flex
YACC    = bison
CFLAGS  = -O2 -Wall

parser.tab.c parser.tab.h: parser.y
	$(YACC) -d parser.y

lexer.c: lexer.l parser.tab.h
	$(LEX) -o $@ $<

driver.o: driver.c parser.tab.h
	$(CC) $(CFLAGS) -c driver.c -o driver.o

../esteira: parser.tab.c lexer.c driver.o
	$(CC) $(CFLAGS) parser.tab.c lexer.c driver.o -lfl -o $@

all: ../esteira

clean:
	rm -f parser.c parser.tab.c parser.tab.h lexer.c driver.o ../esteira
