"""Tests for postprocess_results_lib and postprocess_results CLI."""

import json
import os
import subprocess
import sys
import tempfile
import pytest

from postprocess_results_lib import (
    parse_output,
    postprocess_record,
    get_most_recent_results_file,
    postprocess_file,
)


def test_parse_output_standard():
    stdout = """
====== WARMUP ======
generating primes
warmup_run 1.5629s
warmup_run 1.5746s
==== END WARMUP ====
generating primes
time 1.5656s
time 1.5841s
average 1.57s
"""
    stderr = "\tUser time (seconds): 3.5\n\tExit status: 0\n"
    warmup, test = parse_output(stdout, stderr)
    assert warmup == [1.5629, 1.5746]
    assert test == [1.5656, 1.5841]


def test_parse_output_variations():
    stdout = """
warmup_run 0.123
time 0.456
WARMUP_RUN 1e-3s
TIME 2.5s
"""
    stderr = None
    warmup, test = parse_output(stdout, stderr)
    assert warmup == [0.123, 0.001]
    assert test == [0.456, 2.5]


def test_parse_output_empty():
    warmup, test = parse_output(None, "")
    assert warmup == []
    assert test == []


def test_parse_output_ignores_unrelated_times():
    stdout = """
round 0: new_clusters: 0.0000
generated all frames in 2.2662s
average time per frame: 0.2266s
average 1.5569s
minimum 1.5265s
maximum 1.6045s
std dev 0.0256s
total   31.1373s
end-to-end 31.1378s
"""
    stderr = "\tUser time (seconds): 37.13\n\tElapsed (wall clock) time (h:mm:ss or m:ss): 0:37.39\n"
    warmup, test = parse_output(stdout, stderr)
    assert warmup == []
    assert test == []


def test_postprocess_record():
    record = {
        "tag": "primes",
        "bench": "primes",
        "config": "mlton",
        "stdout": "warmup_run 1.2s\ntime 3.4s\n",
        "stderr": "some log\n",
        "elapsed": 10.5,
        "returncode": 0,
    }
    processed = postprocess_record(record)

    assert "stdout" not in processed
    assert "stderr" not in processed
    assert processed["tag"] == "primes"
    assert processed["bench"] == "primes"
    assert processed["config"] == "mlton"
    assert processed["elapsed"] == 10.5
    assert processed["returncode"] == 0
    assert processed["warmup_result_secs"] == [1.2]
    assert processed["test_results_secs"] == [3.4]


def test_get_most_recent_results_file(tmp_path):
    f1 = tmp_path / "260101-100000"
    f2 = tmp_path / "260101-110000"
    f_processed = tmp_path / "260101-110000.processed.jsonl"

    f1.write_text("{}")
    f2.write_text("{}")
    f_processed.write_text("{}")

    os.utime(f1, (1000, 1000))
    os.utime(f2, (2000, 2000))
    os.utime(f_processed, (3000, 3000))

    most_recent = get_most_recent_results_file(str(tmp_path))
    assert most_recent == str(f2)


def test_golden_postprocess(tmp_path):
    testdata_dir = os.path.join(os.path.dirname(__file__), "testdata")
    sample_file = os.path.join(testdata_dir, "sample_results.jsonl")
    golden_file = os.path.join(testdata_dir, "sample_results.golden.jsonl")

    output_file = str(tmp_path / "out.processed.jsonl")
    postprocess_file(infile=sample_file, outfile=output_file)

    with open(output_file, "r") as f_out, open(golden_file, "r") as f_gold:
        out_lines = [json.loads(line) for line in f_out if line.strip()]
        gold_lines = [json.loads(line) for line in f_gold if line.strip()]

    assert out_lines == gold_lines


def test_cli_custom_paths(tmp_path):
    infile = tmp_path / "test_in.jsonl"
    outfile = tmp_path / "test_out.jsonl"

    rec = {
        "tag": "test",
        "stdout": "warmup_run 0.5s\ntime 1.0s\n",
        "stderr": "",
    }
    infile.write_text(json.dumps(rec) + "\n")

    res = subprocess.run(
        [sys.executable, "postprocess_results.py", f"--infile={infile}", f"--outfile={outfile}"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert outfile.exists()

    data = json.loads(outfile.read_text().strip())
    assert "stdout" not in data
    assert "stderr" not in data
    assert data["warmup_result_secs"] == [0.5]
    assert data["test_results_secs"] == [1.0]


def test_cli_singular_script_entrypoint(tmp_path):
    infile = tmp_path / "test_in.jsonl"
    outfile = tmp_path / "test_out.jsonl"

    rec = {
        "tag": "test",
        "stdout": "warmup_run 0.2s\ntime 0.8s\n",
        "stderr": "",
    }
    infile.write_text(json.dumps(rec) + "\n")

    res = subprocess.run(
        [sys.executable, "postprocess_result.py", f"--infile={infile}", f"--outfile={outfile}"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert outfile.exists()

    data = json.loads(outfile.read_text().strip())
    assert data["warmup_result_secs"] == [0.2]
    assert data["test_results_secs"] == [0.8]
