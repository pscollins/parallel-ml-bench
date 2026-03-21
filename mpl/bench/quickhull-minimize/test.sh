set -x
TEMPFILE=$(mktemp)
make clean
make bin/quickhull.bin 2>&1 | tee $TEMPFILE
grep "Found forbidden tuple operations" $TEMPFILE
