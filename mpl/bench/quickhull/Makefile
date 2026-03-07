MPL ?= ~/code/mpl/build/bin/mpl
MPL_FLAGS ?= -default-type int64 -default-type word64 -mlb-path-var 'COMPAT mpl'

.PHONY: all clean run

all: quickhull.bin

quickhull.bin: *.sml quickhull.mlb ../../lib.mlb
	$(MPL) $(MPL_FLAGS) -output quickhull.bin quickhull.mlb

run: quickhull.bin
	./quickhull.bin -n 10000

clean:
	rm -f quickhull.bin
