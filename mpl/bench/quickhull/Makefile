MPL ?= $(HOME)/code/mpl/build/bin/mpl
EXTRA_MPL_FLAGS ?= 
MPL_FLAGS ?= -default-type int64 -default-type word64 -mlb-path-var 'COMPAT mpl'
BINARY_FLAGS ?= -n 10000

.PHONY: all clean run

all: bin/quickhull.bin

bin/quickhull.bin: *.sml quickhull.mlb ../../lib.mlb
	mkdir -p bin
	cd bin && $(MPL) $(MPL_FLAGS) $(EXTRA_MPL_FLAGS) -output quickhull.bin ../quickhull.mlb

run: bin/quickhull.bin
	./bin/quickhull.bin $(BINARY_FLAGS)

clean:
	rm -rf bin
