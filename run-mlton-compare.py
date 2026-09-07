#!/usr/bin/env python3

import argparse
import collections
import filecmp
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


def prebuild_binaries(root, matching_rows, test_config, base_config, extra_flags=None):
    bins_by_place = collections.defaultdict(set)
    for row in matching_rows:
        bench = row.get("bench")
        if not bench:
            continue
        cwd = row.get("cwd", "mpl")
        place = os.path.join(root, cwd)
        bins_by_place[place].add(f"{bench}.{test_config}.bin")
        bins_by_place[place].add(f"{bench}.{base_config}.bin")

    ncpu = os.cpu_count() or 4
    jobs = int(max(4, ncpu / 2))

    for place, bins in bins_by_place.items():
        if not bins:
            continue
        bin_list = sorted(list(bins))
        print(f"[INFO] Building {len(bin_list)} binaries in {place}: {', '.join(bin_list)}")
        make_cmd = ["make", "-C", place, f"-j{jobs}"]
        if extra_flags is not None:
            make_cmd.append(f"EXTRA_FLAGS={extra_flags}")
        make_cmd += bin_list
        res = subprocess.run(make_cmd)
        if res.returncode != 0:
            sys.stderr.write(f"[ERR] Build failed in {place}\n")
            sys.exit(res.returncode)


def filter_identical_binaries(root, matching_rows, test_config, base_config):
    identical_benchmarks = set()
    unique_benches = set((row.get("cwd", "mpl"), row.get("bench")) for row in matching_rows if row.get("bench"))
    for cwd, bench in sorted(unique_benches):
        bin_test = os.path.join(root, cwd, "bin", f"{bench}.{test_config}.bin")
        bin_base = os.path.join(root, cwd, "bin", f"{bench}.{base_config}.bin")

        if not os.path.isfile(bin_test) or not os.path.isfile(bin_base):
            print(f"[WARN] Missing binary for '{bench}': {bin_test} or {bin_base}")
            continue

        if filecmp.cmp(bin_test, bin_base, shallow=False):
            print(f"[INFO] Skipping benchmark '{bench}': '{test_config}' and '{base_config}' binaries are identical")
            identical_benchmarks.add((cwd, bench))
        else:
            print(f"[INFO] Running benchmark '{bench}': '{test_config}' and '{base_config}' binaries differ")

    return [
        row for row in matching_rows
        if (row.get("cwd", "mpl"), row.get("bench")) not in identical_benchmarks
    ]


def create_parser():
    parser = argparse.ArgumentParser(description="Run MLton compare experiments.")
    parser.add_argument('--test', default='.*', help="Benchmark test name pattern (regex)")
    parser.add_argument('--base_config', default='mlton-baseline', help="Base config name")
    parser.add_argument('--test_config', default='mlton', help="Test config name")
    parser.add_argument('--extra_flags', '--extra-flags', default=None, help="Extra flags to pass to make (sets EXTRA_FLAGS)")
    parser.add_argument(
        '--filter_identical_binaries',
        dest='filter_identical_binaries',
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip tests for benchmarks where generated binaries are identical (default: True)"
    )
    parser.add_argument(
        '--no_filter_identical_binaries',
        dest='filter_identical_binaries',
        action='store_false',
        help=argparse.SUPPRESS
    )
    return parser


def main():
    parser = create_parser()
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

    prebuild_binaries(root, matching_rows, args.test_config, args.base_config, args.extra_flags)

    if args.filter_identical_binaries:
        active_rows = filter_identical_binaries(
            root, matching_rows, args.test_config, args.base_config
        )
        if not active_rows:
            print("[INFO] All benchmark binaries are identical; no tests to run.")
            sys.exit(0)
    else:
        active_rows = matching_rows

    # Run experiments for both test_config and base_config
    run_rows = []
    for row in active_rows:
        r_test = row.copy()
        r_test["config"] = args.test_config
        if "cmd" in r_test:
            r_test["cmd"] = r_test["cmd"].replace(".mpl.bin", f".{args.test_config}.bin", 1)
        run_rows.append(r_test)

    for row in active_rows:
        r_base = row.copy()
        r_base["config"] = args.base_config
        if "cmd" in r_base:
            r_base["cmd"] = r_base["cmd"].replace(".mpl.bin", f".{args.base_config}.bin", 1)
        run_rows.append(r_base)

    run_input = "\n".join(json.dumps(r) for r in run_rows) + "\n"

    run_cmd = [run, "--output", results]
    res = subprocess.run(run_cmd, input=run_input, text=True)

    if res.returncode != 0:
        sys.exit(res.returncode)

    print(f"[INFO] wrote results to {results}")


if __name__ == "__main__":
    main()
