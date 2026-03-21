cd $(dirname $0)
TEMPFILE=$(mktemp)
make clean
make bin/quickhull.bin 2>&1 | tee $TEMPFILE
grep -q "Found forbidden tuple operations" $TEMPFILE
