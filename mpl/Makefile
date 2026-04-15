-include Makefile.config

DEFAULT_FLAGS?=-default-type int64 -default-type word64
DUMP_IR_FLAGS=-keep-pass-out-dir "bin/" -keep-pass '.*'
DIAGNOSTIC_FLAGS=-keep-pass-out-dir "bin/" -diag-pass '.*'
PROIFLE_FLAGS=$(DIAGNOSTIC_FLAGS) -keep g

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
	@./run_profile.sh "bin/$@"
