#!/usr/bin/env python3
"""Library for postprocessing parallel-ml-bench JSONL benchmark results."""

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
from typing import Dict, List, Optional, Tuple, Any

WARMUP_PAT = re.compile(r'^\s*warmup_run\s+([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\s*s?\s*$', re.IGNORECASE)
TEST_PAT = re.compile(r'^\s*time\s+([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\s*s?\s*$', re.IGNORECASE)

KNOWN_COMPILER_NAMES = {
    'gcc': ['gcc'],
    'g++': ['g++'],
    'cpp': ['g++', 'gcc'],
    'c++': ['g++', 'gcc'],
    'clang': ['clang'],
    'clang++': ['clang++'],
    'mlton': ['mlton'],
    'mpl': ['mpl'],
    'go': ['go'],
    'java': ['javac', 'java'],
    'ocaml': ['ocamlopt', 'ocamlc'],
}

WRAPPERS = {
    '/usr/bin/time', 'time', 'numactl', 'env', 'taskset',
}


def get_hostname() -> str:
    """Returns system hostname."""
    return socket.gethostname()


def get_git_hash() -> str:
    """Returns current git commit hash or 'unknown' if git execution fails."""
    try:
        out = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL, text=True).strip()
        return out
    except Exception:
        return 'unknown'


def get_md5_via_tool(filepath: str) -> Optional[str]:
    """Calculates MD5 checksum of filepath using md5 or md5sum CLI tool."""
    if not filepath or not os.path.isfile(filepath):
        return None

    for tool in ['md5', 'md5sum']:
        if shutil.which(tool):
            try:
                out = subprocess.check_output([tool, filepath], text=True, stderr=subprocess.DEVNULL)
                m = re.search(r'[a-fA-F0-9]{32}', out)
                if m:
                    return m.group(0).lower()
            except Exception:
                pass

    try:
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def parse_compiler_binary_path(cmd_str: Optional[str] = None, record: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Parses out the compiler binary path from commandline string or record."""
    if not cmd_str and record:
        cmd_str = record.get('cmd') or record.get('commandline') or ''

    if not cmd_str:
        return None

    def resolve_path(p: str) -> Optional[str]:
        p_expanded = os.path.expanduser(p)
        if os.path.isfile(p_expanded):
            return os.path.abspath(p_expanded)
        w = shutil.which(p)
        if w and os.path.isfile(w):
            return os.path.abspath(w)
        return None

    tokens = [t for t in cmd_str.split() if '=' not in t or t.startswith('/') or t.startswith('./')]
    idx = 0
    while idx < len(tokens):
        t = tokens[idx]
        if t in WRAPPERS or os.path.basename(t) in WRAPPERS:
            idx += 1
            while idx < len(tokens) and tokens[idx].startswith('-'):
                idx += 1
                if idx < len(tokens) and tokens[idx - 1] in ('-i', '-c'):
                    idx += 1
            continue
        if t == '--':
            idx += 1
            continue
        break

    if idx < len(tokens):
        exe_token = tokens[idx]
        resolved = resolve_path(exe_token)
        if resolved:
            base = os.path.basename(resolved).lower()
            if any(c in base for c in ['gcc', 'g++', 'clang', 'mlton', 'mpl', 'ocaml', 'javac', 'go', 'compiler']):
                return resolved

    compiler_key = None
    bin_match = re.search(r'bin/[^/\s]+\.([^/\s]+)\.bin', cmd_str)
    if bin_match:
        compiler_key = bin_match.group(1)
    elif record and record.get('config'):
        compiler_key = record.get('config')

    if not compiler_key and idx < len(tokens):
        resolved = resolve_path(tokens[idx])
        if resolved:
            return resolved

    if not compiler_key:
        return None

    base_key = compiler_key.split('-')[0]

    root_dir = os.getcwd()
    try:
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], stderr=subprocess.DEVNULL, text=True).strip()
        if git_root:
            root_dir = git_root
    except Exception:
        pass

    config_candidates = [
        os.path.join(root_dir, 'mpl', 'config', f'{compiler_key}.json'),
        os.path.join(root_dir, 'mpl', 'config', f'{base_key}.json'),
        os.path.join(root_dir, 'config', f'{compiler_key}.json'),
        os.path.join(root_dir, 'config', f'{base_key}.json'),
    ]

    for cfg_path in config_candidates:
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg_data = json.load(f)
                    if 'compiler' in cfg_data:
                        res = resolve_path(cfg_data['compiler'])
                        if res:
                            return res
            except Exception:
                pass

    names_to_try = KNOWN_COMPILER_NAMES.get(compiler_key) or KNOWN_COMPILER_NAMES.get(base_key) or [compiler_key, base_key]
    for name in names_to_try:
        res = resolve_path(name)
        if res:
            return res

    return None


def get_compiler_md5(record: Dict[str, Any]) -> str:
    """Parses out the compiler binary from the commandline in record and calculates its MD5 checksum."""
    compiler_path = parse_compiler_binary_path(record=record)
    if compiler_path:
        md5_hash = get_md5_via_tool(compiler_path)
        if md5_hash:
            return md5_hash
    return 'unknown'


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
    into warmup_result_secs and test_results_secs. Adds compiler_md5 field.
    """
    record_copy = dict(record)
    stdout = record_copy.pop('stdout', None)
    stderr = record_copy.pop('stderr', None)

    warmup_secs, test_secs = parse_output(stdout, stderr)
    record_copy['warmup_result_secs'] = warmup_secs
    record_copy['test_results_secs'] = test_secs
    record_copy['compiler_md5'] = get_compiler_md5(record)
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


def postprocess_file(
    infile: Optional[str] = None,
    nick: str = "",
    results_dir: str = 'results',
    processed_results_dir: str = 'processed_results',
) -> Tuple[str, str]:
    """Reads JSON lines from infile, postprocesses each record, and writes to outfile.

    Defaults infile to the most recent file under results_dir.
    Outfile format: processed_results/<NICK>:<FILENAME>:<HOSTNAME>:<GIT_HASH>:<FILENAME>.processed.jsonl
    """
    if infile is None:
        infile = get_most_recent_results_file(results_dir)

    filename = os.path.basename(infile)
    hostname = get_hostname()
    git_hash = get_git_hash()
    nick_str = nick if nick is not None else ""

    outfile_name = f"{nick_str}:{filename}:{hostname}:{git_hash}:{filename}.processed.jsonl"
    outfile = os.path.join(processed_results_dir, outfile_name)

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


