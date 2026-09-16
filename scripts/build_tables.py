#!/usr/bin/env python3
import sys
import os
import re

def parse_perf_file(filepath):
    """
    Parses perf stat CSV output.
    Returns a dict of metrics.
    """
    metrics = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]

            # Task clock (msec)
            # e.g., 86978.78,msec,task-clock,86978783916,100.00,0.9,CPUs  CPUs_utilized
            if len(parts) > 2 and parts[2] == 'task-clock':
                try:
                    metrics['task_clock_s'] = float(parts[0]) / 1000.0
                except ValueError:
                    pass

            # Instructions
            # e.g., 827402070118,,instructions,37278977797,42.00,3.2,instructions  insn_per_cycle
            if len(parts) > 2 and parts[2] == 'instructions':
                try:
                    metrics['instructions'] = float(parts[0])
                except ValueError:
                    pass

            # CPU cycles
            # e.g., 258438600942,,cpu-cycles,31063079737,35.00,3.0,GHz  cycles_frequency
            if len(parts) > 2 and parts[2] == 'cpu-cycles':
                try:
                    metrics['cpu_cycles'] = float(parts[0])
                except ValueError:
                    pass

            # Branch miss rate
            # e.g., 50011691,,branch-misses,18637296489,21.00,0.0,%  branch_miss_rate
            if 'branch_miss_rate' in line and len(parts) > 5:
                try:
                    metrics['branch_miss_rate'] = float(parts[5].replace('%', '').strip())
                except ValueError:
                    pass

            # L1 D-Cache miss rate
            # e.g., 3980943728,,L1-dcache-load-misses,31064774345,35.00,1.5,%  l1d_miss_rate
            if 'l1d_miss_rate' in line and len(parts) > 5:
                try:
                    metrics['l1d_miss_rate'] = float(parts[5].replace('%', '').strip())
                except ValueError:
                    pass

            # LLC miss rate
            # e.g., 65308192,,LLC-loads,12427302608,14.00,24.7,%  llc_miss_rate
            if 'llc_miss_rate' in line and len(parts) > 5:
                try:
                    metrics['llc_miss_rate'] = float(parts[5].replace('%', '').strip())
                except ValueError:
                    pass

            # dTLB miss rate
            # e.g., 268588084249,,dTLB-loads,37276703210,42.00,0.0,%  dtlb_miss_rate
            if 'dtlb_miss_rate' in line and len(parts) > 5:
                try:
                    metrics['dtlb_miss_rate'] = float(parts[5].replace('%', '').strip())
                except ValueError:
                    pass

            # Topdown L1 metrics:
            # ,,,,,2.0,%  tma_backend_bound
            # ,,,,,94.6,%  tma_bad_speculation
            # ,43485554861,49.00,,,0.1,%  tma_frontend_bound
            # ,49700410234,57.00,,,3.3,%  tma_retiring
            if 'tma_retiring' in line:
                m = re.search(r'([0-9.]+),%\s+tma_retiring', line)
                if m:
                    metrics['retiring'] = float(m.group(1))
            if 'tma_bad_speculation' in line:
                m = re.search(r'([0-9.]+),%\s+tma_bad_speculation', line)
                if m:
                    metrics['bad_speculation'] = float(m.group(1))
            if 'tma_frontend_bound' in line:
                m = re.search(r'([0-9.]+),%\s+tma_frontend_bound', line)
                if m:
                    metrics['frontend_bound'] = float(m.group(1))
            if 'tma_backend_bound' in line:
                m = re.search(r'([0-9.]+),%\s+tma_backend_bound', line)
                if m:
                    metrics['backend_bound'] = float(m.group(1))

    if 'instructions' in metrics and 'cpu_cycles' in metrics and metrics['cpu_cycles'] > 0:
        metrics['ipc'] = metrics['instructions'] / metrics['cpu_cycles']
    else:
        metrics['ipc'] = 0.0

    return metrics


def format_table(base_file, test_file, bench_name, config_name, cores="1"):
    base_m = parse_perf_file(base_file)
    test_m = parse_perf_file(test_file)

    # Calculate Overview
    base_tc = base_m.get('task_clock_s', 0.0)
    test_tc = test_m.get('task_clock_s', 0.0)
    base_tc_round = round(base_tc, 2)
    test_tc_round = round(test_tc, 2)
    tc_diff = ((test_tc_round - base_tc_round) / base_tc_round * 100) if base_tc_round > 0 else 0.0

    base_insn_b = base_m.get('instructions', 0.0) / 1e9
    test_insn_b = test_m.get('instructions', 0.0) / 1e9
    base_insn_round = round(base_insn_b, 2)
    test_insn_round = round(test_insn_b, 2)
    insn_diff = ((test_insn_round - base_insn_round) / base_insn_round * 100) if base_insn_round > 0 else 0.0

    base_ipc = base_m.get('ipc', 0.0)
    test_ipc = test_m.get('ipc', 0.0)
    base_ipc_round = round(base_ipc, 2)
    test_ipc_round = round(test_ipc, 2)
    ipc_diff = ((test_ipc_round - base_ipc_round) / base_ipc_round * 100) if base_ipc_round > 0 else 0.0

    def rate_pp(key):
        b = round(base_m.get(key, 0.0), 1)
        t = round(test_m.get(key, 0.0), 1)
        diff = t - b
        diff_str = f"{diff:+.1f} pp" if abs(diff) >= 0.05 else "0.0 pp"
        return f"{b:.1f}\\%", f"{t:.1f}\\%", diff_str

    bm_base, bm_test, bm_diff = rate_pp('branch_miss_rate')
    l1d_base, l1d_test, l1d_diff = rate_pp('l1d_miss_rate')
    llc_base, llc_test, llc_diff = rate_pp('llc_miss_rate')
    dtlb_base, dtlb_test, dtlb_diff = rate_pp('dtlb_miss_rate')

    ret_base, ret_test, ret_diff = rate_pp('retiring')
    bad_base, bad_test, bad_diff = rate_pp('bad_speculation')
    fe_base, fe_test, fe_diff = rate_pp('frontend_bound')
    be_base, be_test, be_diff = rate_pp('backend_bound')

    core_label = f"{cores}core" if str(cores) == "1" else f"{cores}cores"
    core_text = f"{cores} core" if str(cores) == "1" else f"{cores} cores"

    caption = f"{config_name} performance metric comparison on {core_text} ({bench_name}, {core_text})"
    label = f"tab:perf_comparison_{config_name.lower()}_{bench_name.lower()}_{core_label}"

    table = f"""\\begin{{table}}[htbp]
  \\centering
  \\caption{{{caption}}}
  \\label{{{label}}}
  \\begin{{tabular}}{{lrrr}}
    \\toprule
    \\textbf{{Metric}} & \\textbf{{Baseline}} & \\textbf{{Test}} & \\textbf{{Diff / Change}} \\\\
    \\midrule
    \\multicolumn{{4}}{{l}}{{\\textit{{Execution Overview}}}} \\\\
    \\quad Task Clock (s)           & {base_tc_round:.2f} s   & {test_tc_round:.2f} s   & {tc_diff:+.2f}\\%   \\\\
    \\quad Instructions ($10^9$)    & {base_insn_round:.2f} B  & {test_insn_round:.2f} B  & {insn_diff:+.2f}\\%   \\\\
    \\quad IPC                      & {base_ipc_round:.2f}       & {test_ipc_round:.2f}       & {ipc_diff:+.2f}\\%    \\\\
    \\midrule
    \\multicolumn{{4}}{{l}}{{\\textit{{Rates and Miss Percentages}}}} \\\\
    \\quad Branch Miss Rate         & {bm_base}      & {bm_test}      & {bm_diff}     \\\\
    \\quad L1 D-Cache Miss Rate     & {l1d_base}      & {l1d_test}      & {l1d_diff}    \\\\
    \\quad LLC Load Miss Rate       & {llc_base}     & {llc_test}     & {llc_diff}    \\\\
    \\quad dTLB Load Miss Rate      & {dtlb_base}      & {dtlb_test}      & {dtlb_diff}     \\\\
    \\midrule
    \\multicolumn{{4}}{{l}}{{\\textit{{Topdown L1 Metrics}}}} \\\\
    \\quad Retiring                 & {ret_base}      & {ret_test}      & {ret_diff}    \\\\
    \\quad Bad Speculation          & {bad_base}     & {bad_test}     & {bad_diff}   \\\\
    \\quad Frontend Bound           & {fe_base}      & {fe_test}      & {fe_diff}    \\\\
    \\quad Backend Bound            & {be_base}      & {be_test}      & {be_diff}    \\\\
    \\bottomrule
  \\end{{tabular}}
\\end{{table}}"""
    return table


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: build_tables.py <base_file> <test_file> <bench_name> <config_name> [cores]")
        sys.exit(1)
    base_file = sys.argv[1]
    test_file = sys.argv[2]
    bench_name = sys.argv[3]
    config_name = sys.argv[4]
    cores = sys.argv[5] if len(sys.argv) > 5 else "1"
    print(format_table(base_file, test_file, bench_name, config_name, cores))
