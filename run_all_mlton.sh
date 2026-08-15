#!/bin/bash
set -e

BASE=""

usage() {
  echo "Usage: $0 --base_nick <nick>"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base_nick)
      if [[ -n "$2" && "$2" != --* ]]; then
        BASE="$2"
        shift 2
      else
        echo "Error: --base_nick requires a non-empty argument." >&2
        usage
      fi
      ;;
    --base_nick=*)
      BASE="${1#*=}"
      if [[ -z "$BASE" ]]; then
        echo "Error: --base_nick requires a non-empty argument." >&2
        usage
      fi
      shift 1
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "$BASE" ]]; then
  echo "Error: --base_nick is required." >&2
  usage
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || dirname "$(readlink -f "$0")")"
cd "$ROOT"

FLAVORS=("aos" "con" "soa" "tuple")

for FLAVOR in "${FLAVORS[@]}"; do
  echo "=================================================="
  echo "Running MLton compare for flavor: $FLAVOR (base nick: $BASE)"
  echo "=================================================="
  ./run-mlton-compare.py --test_config="mlton-$FLAVOR" && \
  ./postprocess_results.py --nick="mlton_${FLAVOR}_${BASE}"
done
