MPL ?= ~/code/mpl/build/bin/mpl
MPL_FLAGS ?= -default-type int64 -default-type word64 -mlb-path-var 'COMPAT mpl'

.PHONY: all clean run

all: bin/quickhull.bin

bin/quickhull.bin: *.sml quickhull.mlb ../../lib.mlb
	mkdir -p bin
	$(MPL) $(MPL_FLAGS) -output bin/quickhull.bin quickhull.mlb

run: bin/quickhull.bin
	./bin/quickhull.bin -n 10000

clean:
	rm -rf bin
