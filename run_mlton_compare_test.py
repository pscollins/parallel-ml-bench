import importlib.util
import os
from unittest.mock import patch, MagicMock

# Dynamically import run-mlton-compare.py since it has hyphens in the filename
spec = importlib.util.spec_from_file_location(
    "run_mlton_compare",
    os.path.join(os.path.dirname(__file__), "run-mlton-compare.py")
)
run_mlton_compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_mlton_compare)


def test_parser_extra_flags():
    parser = run_mlton_compare.create_parser()

    # Default
    args, rest = parser.parse_known_args([])
    assert args.extra_flags is None
    assert rest == []

    # Underscored flag
    args, rest = parser.parse_known_args([
        '--extra_flags=-chunkify one',
        '--some_gencmds_flag'
    ])
    assert args.extra_flags == '-chunkify one'
    assert rest == ['--some_gencmds_flag']

    # Hyphenated flag
    args, rest = parser.parse_known_args([
        '--extra-flags', '-pre-flatten-max-iters 10'
    ])
    assert args.extra_flags == '-pre-flatten-max-iters 10'


@patch("subprocess.run")
def test_prebuild_binaries_without_extra_flags(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    matching_rows = [
        {"bench": "primes", "cwd": "mpl"},
        {"bench": "mandelbrot", "cwd": "mpl"}
    ]

    run_mlton_compare.prebuild_binaries(
        root="/fake/root",
        matching_rows=matching_rows,
        test_config="mlton",
        base_config="mlton-baseline",
        extra_flags=None
    )

    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert "make" == called_cmd[0]
    assert "-C" == called_cmd[1]
    assert "/fake/root/mpl" == called_cmd[2]
    assert not any(arg.startswith("EXTRA_FLAGS=") for arg in called_cmd)
    assert "mandelbrot.mlton-baseline.bin" in called_cmd
    assert "mandelbrot.mlton.bin" in called_cmd
    assert "primes.mlton-baseline.bin" in called_cmd
    assert "primes.mlton.bin" in called_cmd


@patch("subprocess.run")
def test_prebuild_binaries_with_extra_flags(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    matching_rows = [
        {"bench": "primes", "cwd": "mpl"}
    ]

    run_mlton_compare.prebuild_binaries(
        root="/fake/root",
        matching_rows=matching_rows,
        test_config="mlton-aos",
        base_config="mlton-baseline",
        extra_flags="-chunkify one -pre-flatten-max-iters 10"
    )

    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert "make" == called_cmd[0]
    assert "-C" == called_cmd[1]
    assert "/fake/root/mpl" == called_cmd[2]
    assert "EXTRA_FLAGS=-chunkify one -pre-flatten-max-iters 10" in called_cmd
    assert "primes.mlton-aos.bin" in called_cmd
    assert "primes.mlton-baseline.bin" in called_cmd


def test_parser_run_under_flags():
    parser = run_mlton_compare.create_parser()

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

    rows = run_mlton_compare.generate_run_rows(
        active_rows,
        test_config="mlton",
        base_config="mlton-baseline",
        test_run_under=None,
        base_run_under=None
    )

    assert len(rows) == 2
    r_test, r_base = rows[0], rows[1]

    assert r_test["config"] == "mlton"
    assert r_test["cmd"] == "/usr/bin/time -v bin/primes.mlton.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert "run_under" not in r_test

    assert r_base["config"] == "mlton-baseline"
    assert r_base["cmd"] == "/usr/bin/time -v bin/primes.mlton-baseline.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert "run_under" not in r_base


def test_generate_run_rows_with_run_under():
    active_rows = [
        {
            "bench": "primes",
            "config": "mpl",
            "cmd": "/usr/bin/time -v bin/primes.mpl.bin @mpl procs 1 set-affinity -- -N 100000000"
        }
    ]

    rows = run_mlton_compare.generate_run_rows(
        active_rows,
        test_config="mlton-aos",
        base_config="mlton-baseline",
        test_run_under="perf stat -a topdown",
        base_run_under="perf stat -a topdown"
    )

    assert len(rows) == 2
    r_test, r_base = rows[0], rows[1]

    assert r_test["config"] == "mlton-aos"
    assert r_test["cmd"] == "perf stat -a topdown /usr/bin/time -v bin/primes.mlton-aos.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert r_test["run_under"] == "perf stat -a topdown"

    assert r_base["config"] == "mlton-baseline"
    assert r_base["cmd"] == "perf stat -a topdown /usr/bin/time -v bin/primes.mlton-baseline.bin @mpl procs 1 set-affinity -- -N 100000000"
    assert r_base["run_under"] == "perf stat -a topdown"

