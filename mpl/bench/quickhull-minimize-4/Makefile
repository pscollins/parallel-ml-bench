MPL ?= $(HOME)/code/mpl/build/bin/mpl
EXTRA_MPL_FLAGS ?= 
MPL_FLAGS ?= -default-type int64 -default-type word64 -mlb-path-var 'COMPAT mpl' -pre-flatten-max-iters 4 -pre-flatten-post-steps 'shrink,flatten,shrink' -polyvariance-small 100000

.PHONY: all clean run

all: bin/quickhull.bin

bin/quickhull.bin: *.sml quickhull.mlb ../../lib.mlb
	mkdir -p bin
	cd bin && $(MPL) $(MPL_FLAGS) $(EXTRA_MPL_FLAGS) -output quickhull.bin ../quickhull.mlb

run: bin/quickhull.bin
	./bin/quickhull.bin -n 10000

clean:
	rm -rf bin
