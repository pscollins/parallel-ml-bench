#!/usr/bin/env python3

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime


def get_git_root():
    try:
        res = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return os.path.abspath(os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(description="Run MLton compare experiments.")
    parser.add_argument('--test', required=True, help="Benchmark test name")

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

    matching_rows = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue

        if (row.get("config") == "mpl" and
            (row.get("bench") == args.test or row.get("tag") == args.test) and
            row.get("exp") == "time"):
            matching_rows.append(row)

    if not matching_rows:
        print(f"[ERR] No experiments found for benchmark '{args.test}'")
        sys.exit(1)

    # Run experiments for both 'mlton' and 'mlton-baseline'
    run_rows = []
    for row in matching_rows:
        r_mlton = row.copy()
        r_mlton["config"] = "mlton"
        if "cmd" in r_mlton:
            r_mlton["cmd"] = r_mlton["cmd"].replace(".mpl.bin", ".mlton.bin", 1)
        run_rows.append(r_mlton)

    for row in matching_rows:
        r_baseline = row.copy()
        r_baseline["config"] = "mlton-baseline"
        if "cmd" in r_baseline:
            r_baseline["cmd"] = r_baseline["cmd"].replace(".mpl.bin", ".mlton-baseline.bin", 1)
        run_rows.append(r_baseline)

    run_input = "\n".join(json.dumps(r) for r in run_rows) + "\n"

    run_cmd = [run, "--compile", "--output", results]
    res = subprocess.run(run_cmd, input=run_input, text=True)

    if res.returncode != 0:
        sys.exit(res.returncode)

    print(f"[INFO] wrote results to {results}")


if __name__ == "__main__":
    main()
