-include Makefile.config

DEFAULT_FLAGS?=-default-type int64 -default-type word64
DUMP_IR_FLAGS=-keep-pass-out-dir "bin/" -keep-pass '.*'
DIAGNOSTIC_FLAGS=-keep-pass-out-dir "bin/" -diag-pass '.*' -keep-pass '.*' -verbose 3
PROFILE_ONLY_FLAGS=-keep g -cc-opt '-g2' -link-opt '-lprofiler'
PROFILE_FLAGS=$(DIAGNOSTIC_FLAGS) $(PROFILE_ONLY_FLAGS)
# EXTRA_FLAGS=-chunkify func -pre-flatten-max-iters 10 -pre-flatten-consumer-policy all_unpack -pre-flatten-resolve-policy global
# EXTRA_FLAGS=-chunkify one -pre-flatten-max-iters 10 -pre-flatten-consumer-policy always -pre-flatten-resolve-policy global -pre-flatten-types-policy any -max-type-print-depth 2 -mlb-path-var 'COMPAT mpl'   -pre-flatten-post-steps shrink,flatten,shrink  -pre-flatten-recursive-steps 10   -polyvariance-small 100000  -type-check true
# EXTRA_FLAGS=-chunkify one -pre-flatten-max-iters 1 -pre-flatten-consumer-policy always -pre-flatten-resolve-policy global -pre-flatten-types-policy any -max-type-print-depth 2 -mlb-path-var 'COMPAT mpl'   -pre-flatten-post-steps shrink,flatten,shrink  -pre-flatten-recursive-steps 10
# EXTRA_FLAGS=-chunkify one -pre-flatten-max-iters 0 -pre-flatten-consumer-policy all_unpack -pre-flatten-resolve-policy global -pre-flatten-types-policy con -pre-flatten-post-steps shrink,flatten,shrink -pre-flatten-recursive-steps 10 -shallow-flatten-policy maxWidth:3
# EXTRA_FLAGS=-chunkify one -pre-flatten-max-iters 0 -pre-flatten-consumer-policy all_unpack -pre-flatten-resolve-policy global -pre-flatten-types-policy con -pre-flatten-post-steps shrink,flatten,shrink -pre-flatten-recursive-steps 10 -shallow-flatten-policy maxWidth:3 -type-check true
# EXTRA_FLAGS=-pre-flatten-max-iters 0 -shallow-flatten-max-iters 1 -shallow-flatten-mechanism aos -shallow-flatten-policy maxWidthSameType:3
EXTRA_FLAGS=
# EXTRA_FLAGS=

.PHONY: all clean realclean phony

default:
	@echo "usage: make <bench>.<config>.bin"

clean:
	rm -f bin/*

phony:

%.bin: phony
	@mkdir -p bin
	@./scripts/compile.py \
		--benchmark $(shell echo $* | cut -d. -f1) \
		--config $(shell echo $* | cut -d. -f2) \
		--output "bin/$@" \
		--verbose \
		-- $(DEFAULT_FLAGS) $(EXTRA_FLAGS)


%.dump_ir.bin: phony
	@mkdir -p bin
	@./scripts/compile.py \
		--benchmark $(shell echo $* | cut -d. -f1) \
		--config $(shell echo $* | cut -d. -f2) \
		--output "bin/$@" \
		--verbose \
		-- $(DEFAULT_FLAGS) $(EXTRA_FLAGS) $(DUMP_IR_FLAGS)


%.diagnostic.bin: phony
	@mkdir -p bin
	@./scripts/compile.py \
		--benchmark $(shell echo $* | cut -d. -f1) \
		--config $(shell echo $* | cut -d. -f2) \
		--output "bin/$@" \
		--verbose \
		-- $(DEFAULT_FLAGS) $(EXTRA_FLAGS) $(DIAGNOSTIC_FLAGS)

%.profile.bin: phony
	@mkdir -p bin
	@./scripts/compile.py \
		--benchmark $(shell echo $* | cut -d. -f1) \
		--config $(shell echo $* | cut -d. -f2) \
		--output "bin/$@" \
		--verbose \
		-- $(DEFAULT_FLAGS) $(EXTRA_FLAGS) $(PROFILE_FLAGS)
