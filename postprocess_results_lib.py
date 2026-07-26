#!/usr/bin/env python3
"""Library for postprocessing parallel-ml-bench JSONL benchmark results."""

import json
import os
import re
from typing import Dict, List, Optional, Tuple, Any

WARMUP_PAT = re.compile(r'^\s*warmup_run\s+([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\s*s?\s*$', re.IGNORECASE)
TEST_PAT = re.compile(r'^\s*time\s+([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\s*s?\s*$', re.IGNORECASE)


def parse_output(stdout: Optional[str], stderr: Optional[str]) -> Tuple[List[float], List[float]]:
    """Parses stdout and stderr to extract warmup and test execution times in seconds."""
    warmup_secs: List[float] = []
    test_secs: List[float] = []

    combined_output = (stdout or '') + '\n' + (stderr or '')
    for line in combined_output.splitlines():
        match_warmup = WARMUP_PAT.match(line)
        if match_warmup:
            warmup_secs.append(float(match_warmup.group(1)))
            continue
        match_test = TEST_PAT.match(line)
        if match_test:
            test_secs.append(float(match_test.group(1)))
            continue

    return warmup_secs, test_secs


def postprocess_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Processes a single benchmark record dictionary.

    Keeps all existing tags/fields except for stdout and stderr, which are parsed
    into warmup_result_secs and test_results_secs.
    """
    record_copy = dict(record)
    stdout = record_copy.pop('stdout', None)
    stderr = record_copy.pop('stderr', None)

    warmup_secs, test_secs = parse_output(stdout, stderr)
    record_copy['warmup_result_secs'] = warmup_secs
    record_copy['test_results_secs'] = test_secs
    return record_copy


def get_most_recent_results_file(results_dir: str = 'results') -> str:
    """Finds the most recently modified file in results_dir excluding .processed.jsonl and hidden files."""
    if not os.path.isdir(results_dir):
        raise FileNotFoundError(f"Results directory '{results_dir}' does not exist.")

    candidates = [
        os.path.join(results_dir, f)
        for f in os.listdir(results_dir)
        if os.path.isfile(os.path.join(results_dir, f))
        and not f.endswith('.processed.jsonl')
        and not f.startswith('.')
    ]

    if not candidates:
        raise FileNotFoundError(f"No result files found under '{results_dir}'.")

    candidates.sort(key=lambda path: os.path.getmtime(path), reverse=True)
    return candidates[0]


def postprocess_file(infile: Optional[str] = None, outfile: Optional[str] = None, results_dir: str = 'results') -> Tuple[str, str]:
    """Reads JSON lines from infile, postprocesses each record, and writes to outfile.

    Defaults infile to the most recent file under results_dir.
    Defaults outfile to infile + '.processed.jsonl'.
    """
    if infile is None:
        infile = get_most_recent_results_file(results_dir)

    if outfile is None:
        outfile = f"{infile}.processed.jsonl"

    processed_records = []
    with open(infile, 'r', encoding='utf-8') as f_in:
        for line in f_in:
            line_str = line.strip()
            if not line_str:
                continue
            record = json.loads(line_str)
            processed_record = postprocess_record(record)
            processed_records.append(processed_record)

    os.makedirs(os.path.dirname(os.path.abspath(outfile)), exist_ok=True)
    with open(outfile, 'w', encoding='utf-8') as f_out:
        for record in processed_records:
            f_out.write(json.dumps(record) + '\n')

    return infile, outfile
