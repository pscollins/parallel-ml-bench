#!/bin/bash

# Call as: ./run_profile $MPL_INVOCATION
#
# then run:
#
#  ~/go/bin/pprof -http=localhost:8080 bin/output.prof
export CPUPROFILE=bin/output.prof
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libprofiler.so
$@
