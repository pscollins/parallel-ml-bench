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
    get_md5_via_tool,
    parse_compiler_binary_path,
    get_compiler_md5,
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
        "cmd": "/usr/bin/time -v bin/primes.mlton.bin -N 100000000",
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
    assert "compiler_md5" in processed
    assert isinstance(processed["compiler_md5"], str)
    assert len(processed["compiler_md5"]) > 0


def test_get_md5_via_tool(tmp_path):
    test_file = tmp_path / "sample_binary.bin"
    test_file.write_bytes(b"hello world")
    checksum = get_md5_via_tool(str(test_file))
    # MD5 of 'hello world' is 5eb63bbbe01eeed093cb22bb8f5acdc3
    assert checksum == "5eb63bbbe01eeed093cb22bb8f5acdc3"


def test_parse_compiler_binary_path(tmp_path):
    fake_compiler = tmp_path / "fake_gcc"
    fake_compiler.write_text("#!/bin/sh\necho gcc")
    fake_compiler.chmod(0o755)

    res = parse_compiler_binary_path(f"{fake_compiler} -O3 main.c")
    assert res == str(fake_compiler)

    res_mlton = parse_compiler_binary_path("/usr/bin/time -v bin/primes.mlton.bin -N 100")
    assert res_mlton is not None and ("mlton" in res_mlton)


def test_get_compiler_md5(tmp_path):
    fake_compiler = tmp_path / "fake_compiler"
    fake_compiler.write_bytes(b"test compiler binary content")
    fake_compiler.chmod(0o755)

    record = {
        "cmd": f"{fake_compiler} -o out main.c"
    }
    md5_hash = get_compiler_md5(record)
    assert md5_hash == get_md5_via_tool(str(fake_compiler))


def test_get_most_recent_results_file(tmp_path):
    f1 = tmp_path / "260101-100000"
    f2 = tmp_path / "260101-110000"

    f1.write_text("{}")
    f2.write_text("{}")

    os.utime(f1, (1000, 1000))
    os.utime(f2, (2000, 2000))

    most_recent = get_most_recent_results_file(str(tmp_path))
    assert most_recent == str(f2)


def test_default_output_location(tmp_path, monkeypatch):
    results_dir = tmp_path / "results"
    processed_dir = tmp_path / "processed_results"
    results_dir.mkdir()

    infile = results_dir / "260726-000000"
    infile.write_text(json.dumps({"tag": "test", "stdout": "time 1.2s\n", "stderr": ""}) + "\n")

    monkeypatch.setattr("postprocess_results_lib.get_hostname", lambda: "testhost")
    monkeypatch.setattr("postprocess_results_lib.get_git_hash", lambda: "abc123hash")

    in_res, out_res = postprocess_file(
        infile=str(infile),
        nick="mynick",
        results_dir=str(results_dir),
        processed_results_dir=str(processed_dir),
    )

    expected_outfile = str(processed_dir / "mynick:260726-000000:testhost:abc123hash:260726-000000.processed.jsonl")
    assert out_res == expected_outfile
    assert os.path.exists(expected_outfile)

    data = json.loads(open(expected_outfile).read().strip())
    assert data["test_results_secs"] == [1.2]
    assert "compiler_md5" in data


def test_golden_postprocess(tmp_path, monkeypatch):
    testdata_dir = os.path.join(os.path.dirname(__file__), "testdata")
    sample_file = os.path.join(testdata_dir, "sample_results.jsonl")
    golden_file = os.path.join(testdata_dir, "sample_results.golden.jsonl")

    monkeypatch.setattr("postprocess_results_lib.get_hostname", lambda: "testhost")
    monkeypatch.setattr("postprocess_results_lib.get_git_hash", lambda: "abc123hash")

    in_res, output_file = postprocess_file(
        infile=sample_file,
        nick="testnick",
        processed_results_dir=str(tmp_path),
    )

    filename = os.path.basename(sample_file)
    expected_outfile = str(tmp_path / f"testnick:{filename}:testhost:abc123hash:{filename}.processed.jsonl")
    assert output_file == expected_outfile

    with open(output_file, "r") as f_out, open(golden_file, "r") as f_gold:
        out_lines = [json.loads(line) for line in f_out if line.strip()]
        gold_lines = [json.loads(line) for line in f_gold if line.strip()]

    assert out_lines == gold_lines


def test_cli_nick_option(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    infile = results_dir / "260726-100000"
    rec = {
        "tag": "test",
        "stdout": "warmup_run 0.5s\ntime 1.0s\n",
        "stderr": "",
    }
    infile.write_text(json.dumps(rec) + "\n")

    res = subprocess.run(
        [sys.executable, "postprocess_results.py", f"--infile={infile}", "--nick=mynick"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    filename = os.path.basename(infile)
    output_path = res.stdout.split("->")[-1].strip()
    if os.path.exists(output_path):
        os.remove(output_path)
    assert f"Processed results: {infile} -> processed_results/mynick:{filename}:" in res.stdout
    assert f":{filename}.processed.jsonl" in res.stdout


def test_cli_singular_script_entrypoint(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    infile = results_dir / "260726-200000"
    rec = {
        "tag": "test",
        "stdout": "warmup_run 0.2s\ntime 0.8s\n",
        "stderr": "",
    }
    infile.write_text(json.dumps(rec) + "\n")

    res = subprocess.run(
        [sys.executable, "postprocess_result.py", f"--infile={infile}", "--nick=single_test"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    filename = os.path.basename(infile)
    output_path = res.stdout.split("->")[-1].strip()
    if os.path.exists(output_path):
        os.remove(output_path)
    assert f"Processed results: {infile} -> processed_results/single_test:{filename}:" in res.stdout
    assert f":{filename}.processed.jsonl" in res.stdout


def test_report_mpl_compare_cores_filter(tmp_path):
    infile = tmp_path / "sample_mpl_results"
    records = [
        {"tag": "tokens", "bench": "tokens", "config": "mpl-baseline", "exp": "time", "procs": "1", "stdout": "time 1.0s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl", "exp": "time", "procs": "1", "stdout": "time 0.9s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl-baseline", "exp": "time", "procs": "8", "stdout": "time 0.2s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl", "exp": "time", "procs": "8", "stdout": "time 0.18s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl-baseline", "exp": "time", "procs": "64", "stdout": "time 0.05s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl", "exp": "time", "procs": "64", "stdout": "time 0.04s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl-baseline", "exp": "time", "procs": "160", "stdout": "time 0.03s\n", "stderr": ""},
        {"tag": "tokens", "bench": "tokens", "config": "mpl", "exp": "time", "procs": "160", "stdout": "time 0.025s\n", "stderr": ""},
    ]
    with open(infile, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Filter single core count
    res_160 = subprocess.run(
        [sys.executable, "./report-mpl-compare", str(infile), "--cores=160"],
        capture_output=True,
        text=True,
    )
    assert res_160.returncode == 0
    assert "T(160)" in res_160.stdout
    assert "T(1)" not in res_160.stdout
    assert "T(64)" not in res_160.stdout

    # Filter multiple core counts
    res_1_64 = subprocess.run(
        [sys.executable, "./report-mpl-compare", str(infile), "--cores", "1,64"],
        capture_output=True,
        text=True,
    )
    assert res_1_64.returncode == 0
    assert "T(1)" in res_1_64.stdout
    assert "T(64)" in res_1_64.stdout
    assert "T(160)" not in res_1_64.stdout
    assert "T(8)" not in res_1_64.stdout

    # Invalid core argument
    res_err = subprocess.run(
        [sys.executable, "./report-mpl-compare", str(infile), "--cores", "abc"],
        capture_output=True,
        text=True,
    )
    assert res_err.returncode == 1
    assert "Invalid --cores argument" in res_err.stderr
