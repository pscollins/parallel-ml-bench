cd $(dirname $0)
TEMPFILE=$(mktemp)
make clean
make bin/quickhull.bin 2>&1 | tee $TEMPFILE
if grep -q "Found forbidden tuple operations" $TEMPFILE; then
    echo "Test PASS -- bug still present!"
    exit 0
else
    echo "Test FAIL! BUG NO LONGER REPRODUCES!"
    exit 1
fi
