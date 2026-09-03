import importlib.util
import os
import pytest

# Dynamically import run-mpl-compare.py since it has hyphens in the filename
spec = importlib.util.spec_from_file_location(
    "run_mpl_compare",
    os.path.join(os.path.dirname(__file__), "run-mpl-compare.py")
)
run_mpl_compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_mpl_compare)


def test_parser_run_under_flags():
    parser = run_mpl_compare.create_parser()

    # Test underscored flags
    args, rest = parser.parse_known_args([
        '--base_run_under=perf stat -a topdown',
        '--test_run_under=perf stat -e cycles',
        '--extra_gencmds_arg'
    ])
    assert args.base_run_under == 'perf stat -a topdown'
    assert args.test_run_under == 'perf stat -e cycles'
    assert rest == ['--extra_gencmds_arg']

    # Test hyphenated flags
    args, rest = parser.parse_known_args([
        '--base-run-under', 'FOO',
        '--test-run-under', 'BAR',
    ])
    assert args.base_run_under == 'FOO'
    assert args.test_run_under == 'BAR'

    # Test common run_under flag
    args, _ = parser.parse_known_args([
        '--run_under', 'perf stat'
    ])
    assert args.run_under == 'perf stat'


def test_generate_run_rows_without_run_under():
    active_rows = [
        {
            "bench": "primes",
            "config": "mpl",
            "cmd": "/usr/bin/time -v bin/primes.mpl.bin @mpl procs 1 set-affinity -- -N 100000000"
        }
    ]

    rows = run_mpl_compare.generate_run_rows(
        active_rows,
        test_config="mpl",
        base_config="mpl-baseline",
        test_run_under=None,
        base_run_under=None
    )

    assert len(rows) == 2
    r_test, r_base = rows[0], rows[1]

    assert r_test["config"] == "mpl"
    assert r_test["cmd"] == "/usr/bin/time -v bin/primes.mpl.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert "run_under" not in r_test

    assert r_base["config"] == "mpl-baseline"
    assert r_base["cmd"] == "/usr/bin/time -v bin/primes.mpl-baseline.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert "run_under" not in r_base


def test_generate_run_rows_with_run_under():
    active_rows = [
        {
            "bench": "primes",
            "config": "mpl",
            "cmd": "/usr/bin/time -v bin/primes.mpl.bin @mpl procs 1 set-affinity -- -N 100000000"
        }
    ]

    rows = run_mpl_compare.generate_run_rows(
        active_rows,
        test_config="mpl-opt",
        base_config="mpl-baseline",
        test_run_under="perf stat -a topdown",
        base_run_under="perf stat -a topdown"
    )

    assert len(rows) == 2
    r_test, r_base = rows[0], rows[1]

    assert r_test["config"] == "mpl-opt"
    assert r_test["cmd"] == "perf stat -a topdown /usr/bin/time -v bin/primes.mpl-opt.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert r_test["run_under"] == "perf stat -a topdown"

    assert r_base["config"] == "mpl-baseline"
    assert r_base["cmd"] == "perf stat -a topdown /usr/bin/time -v bin/primes.mpl-baseline.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert r_base["run_under"] == "perf stat -a topdown"


def test_generate_run_rows_different_run_under():
    active_rows = [
        {
            "bench": "msort",
            "config": "mpl",
            "cmd": "/usr/bin/time -v bin/msort.mpl.bin @mpl procs 1"
        }
    ]

    rows = run_mpl_compare.generate_run_rows(
        active_rows,
        test_config="mpl",
        base_config="mpl-baseline",
        test_run_under="perf stat -a topdown",
        base_run_under="taskset -c 0-3"
    )

    assert len(rows) == 2
    r_test, r_base = rows[0], rows[1]

    assert r_test["cmd"] == "perf stat -a topdown /usr/bin/time -v bin/msort.mpl.bin @mpl procs 1"
    assert r_test["run_under"] == "perf stat -a topdown"

    assert r_base["cmd"] == "taskset -c 0-3 /usr/bin/time -v bin/msort.mpl-baseline.bin @mpl procs 1"
    assert r_base["run_under"] == "taskset -c 0-3"


def test_generate_run_rows_whitespace_handling():
    active_rows = [
        {
            "bench": "msort",
            "config": "mpl",
            "cmd": "/usr/bin/time -v bin/msort.mpl.bin @mpl"
        }
    ]

    rows = run_mpl_compare.generate_run_rows(
        active_rows,
        test_config="mpl",
        base_config="mpl-baseline",
        test_run_under="   perf stat   ",
        base_run_under="   "
    )

    r_test, r_base = rows[0], rows[1]
    assert r_test["cmd"] == "perf stat /usr/bin/time -v bin/msort.mpl.bin @mpl"
    assert r_test["run_under"] == "perf stat"

    assert r_base["cmd"] == "/usr/bin/time -v bin/msort.mpl-baseline.bin @mpl"
    assert "run_under" not in r_base
