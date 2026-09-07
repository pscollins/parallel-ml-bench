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
