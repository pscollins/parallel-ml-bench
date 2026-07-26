#!/usr/bin/env python3
"""CLI script to postprocess benchmark results JSONL files."""

import argparse
import sys
from postprocess_results_lib import postprocess_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Postprocess benchmark results JSONL files.")
    parser.add_argument(
        "--infile",
        type=str,
        default=None,
        help="Input JSONL results file (defaults to most-recent file under results/).",
    )
    parser.add_argument(
        "--outfile",
        type=str,
        default=None,
        help="Output JSONL results file (defaults to processed_results/$FILENAME.processed.jsonl).",
    )

    args = parser.parse_args()

    try:
        infile, outfile = postprocess_file(infile=args.infile, outfile=args.outfile)
        print(f"Processed results: {infile} -> {outfile}")
    except Exception as e:
        print(f"Error postprocessing results: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
