#!/usr/bin/env python3

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime


def get_git_root():
    script_dir = os.path.abspath(os.path.dirname(__file__))
    try:
        res = subprocess.run(
            ['git', '-C', script_dir, 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return script_dir


def main():
    parser = argparse.ArgumentParser(description="Run MLton compare experiments.")
    parser.add_argument('--test', default='.*', help="Benchmark test name pattern (regex)")
    parser.add_argument('--base_config', default='mlton-baseline', help="Base config name")
    parser.add_argument('--test_config', default='mlton', help="Test config name")

    args, gencmds_args = parser.parse_known_args()

    root = get_git_root()
    gen = os.path.join(root, "scripts", "gencmds")
    run = os.path.join(root, "scripts", "runcmds")

    now = datetime.now().strftime('%y%m%d-%H%M%S')
    results_dir = os.path.join(root, "results")
    os.makedirs(results_dir, exist_ok=True)
    results = os.path.join(results_dir, now)

    # Clean old binaries
    for bin_path in glob.glob(os.path.join(root, "mpl", "bin", "*.bin")):
        try:
            os.remove(bin_path)
        except OSError:
            pass

    # Get experiments for 'mlton'
    exp_spec = os.path.join(root, "exp-small-mlton.json")
    gen_cmd = [gen] + gencmds_args + [exp_spec]

    try:
        res = subprocess.run(gen_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(e.stderr)
        sys.exit(e.returncode)

    test_pattern = re.compile(args.test)
    matching_rows = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue

        bench = row.get("bench") or ""
        tag = row.get("tag") or ""
        if (row.get("config") == "mpl" and
            (test_pattern.search(bench) or test_pattern.search(tag)) and
            row.get("exp") == "time"):
            matching_rows.append(row)

    if not matching_rows:
        print(f"[ERR] No experiments found for benchmark pattern '{args.test}'")
        sys.exit(1)

    # Run experiments for both test_config and base_config
    run_rows = []
    for row in matching_rows:
        r_test = row.copy()
        r_test["config"] = args.test_config
        if "cmd" in r_test:
            r_test["cmd"] = r_test["cmd"].replace(".mpl.bin", f".{args.test_config}.bin", 1)
        run_rows.append(r_test)

    for row in matching_rows:
        r_base = row.copy()
        r_base["config"] = args.base_config
        if "cmd" in r_base:
            r_base["cmd"] = r_base["cmd"].replace(".mpl.bin", f".{args.base_config}.bin", 1)
        run_rows.append(r_base)

    run_input = "\n".join(json.dumps(r) for r in run_rows) + "\n"

    run_cmd = [run, "--compile", "--output", results]
    res = subprocess.run(run_cmd, input=run_input, text=True)

    if res.returncode != 0:
        sys.exit(res.returncode)

    print(f"[INFO] wrote results to {results}")


if __name__ == "__main__":
    main()
