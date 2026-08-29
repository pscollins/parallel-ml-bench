#!/bin/bash
set -e

BASE=""
FLAVORS_ARG="aos,con,soa,tuple"

usage() {
  echo "Usage: $0 --base_nick <nick> [--flavors <flavors>]"
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
    --flavors)
      if [[ -n "$2" && "$2" != --* ]]; then
        FLAVORS_ARG="$2"
        shift 2
      else
        echo "Error: --flavors requires a non-empty argument." >&2
        usage
      fi
      ;;
    --flavors=*)
      FLAVORS_ARG="${1#*=}"
      if [[ -z "$FLAVORS_ARG" ]]; then
        echo "Error: --flavors requires a non-empty argument." >&2
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

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR")"
cd "$ROOT"

IFS=',' read -r -a FLAVORS <<< "$FLAVORS_ARG"

for FLAVOR in "${FLAVORS[@]}"; do
  FLAVOR="${FLAVOR//[[:space:]]/}"
  CONFIG_FLAVOR="$FLAVOR"
  if [[ "$CONFIG_FLAVOR" == "conapp" ]]; then
    CONFIG_FLAVOR="con"
  fi
  echo "=================================================="
  echo "Running MLton compare for flavor: $CONFIG_FLAVOR (base nick: $BASE)"
  echo "=================================================="
  ./run-mlton-compare.py --test_config="mlton-$CONFIG_FLAVOR" && \
  ./postprocess_results.py --nick="mlton_${CONFIG_FLAVOR}_${BASE}"
done
