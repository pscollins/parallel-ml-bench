#!/bin/bash
set -e

mkdir -p perf_data

for test in delaunay linearrec; do
  for config in aos soa; do
    if [ "$test" = "delaunay" ]; then
      if [ "$config" = "aos" ]; then
        DELAY=107000
      else
        DELAY=108000
      fi
    elif [ "$test" = "linearrec" ]; then
      DELAY=9000
    fi

    export PERF="perf stat -dd -D $DELAY -x ,"
    echo "================================================================================"
    echo "[INFO] Running $test $config with DELAY=$DELAY"
    echo "================================================================================"

    python3 ./run-mlton-compare.py \
      --test_config=mlton-${config} \
      --test=$test \
      --base_run_under="$PERF -o /tmp/${test}_${config}_base.txt" \
      --test_run_under="$PERF -o /tmp/${test}_${config}_test.txt" 2>&1 | tee perf_data/${test}_${config}_output.txt

    cp /tmp/${test}_${config}_base.txt perf_data/${test}_${config}_base.txt
    cp /tmp/${test}_${config}_test.txt perf_data/${test}_${config}_test.txt
    echo "[INFO] Finished $test $config"
  done
done

echo "================================================================================"
echo "[INFO] All 4 experiments complete. Building LaTeX tables..."
echo "================================================================================"

# Build LaTeX tables
cat << 'EOF' > perf_data/tables_new.tex
EOF

python3 scripts/build_tables.py perf_data/delaunay_aos_base.txt perf_data/delaunay_aos_test.txt Delaunay AoS 1 >> perf_data/tables_new.tex
echo "" >> perf_data/tables_new.tex
python3 scripts/build_tables.py perf_data/delaunay_soa_base.txt perf_data/delaunay_soa_test.txt Delaunay SoA 1 >> perf_data/tables_new.tex
echo "" >> perf_data/tables_new.tex
python3 scripts/build_tables.py perf_data/linearrec_aos_base.txt perf_data/linearrec_aos_test.txt Linearrec AoS 1 >> perf_data/tables_new.tex
echo "" >> perf_data/tables_new.tex
python3 scripts/build_tables.py perf_data/linearrec_soa_base.txt perf_data/linearrec_soa_test.txt Linearrec SoA 1 >> perf_data/tables_new.tex
echo "" >> perf_data/tables_new.tex

echo "[INFO] Tables successfully generated in perf_data/tables_new.tex"
