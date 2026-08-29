#!/usr/bin/env bash
# Run cu-perceive on Windows Python from WSL (or Windows bash).
# Zero hardcoded paths (M1): CU_ROOT derives from this script's location;
# the interpreter comes from CU_PYTHON or PATH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CU_ROOT="$(dirname "$SCRIPT_DIR")"

# 1. Interpreter: CU_PYTHON env wins; else probe python.exe on PATH.
#    Give CU_PYTHON a full path to a Windows python.exe, e.g.
#    CU_PYTHON=/mnt/c/Users/you/miniconda3/python.exe ./bin/cu-perceive.sh windows
PY="${CU_PYTHON:-}"
if [[ -z "$PY" ]]; then
  if command -v python.exe >/dev/null 2>&1; then
    PY="$(command -v python.exe)"
  else
    echo "cu-perceive: no Windows python found. Set CU_PYTHON to a full path of a Windows python.exe" >&2
    exit 2
  fi
fi

# 2. PYTHONPATH in the interpreter's own path space: translate Linux repo
#    paths (WSL view) to Windows paths when the interpreter is a Windows exe.
win() {
  local p="$1"
  case "$p" in
    /*)
      case "$PY" in
        *.exe|/mnt/*)
          if command -v wslpath >/dev/null 2>&1; then wslpath -w "$p"; else echo "$p"; fi ;;
        *) echo "$p" ;;
      esac ;;
    *) echo "$p" ;;
  esac
}

export PYTHONPATH="$(win "$CU_ROOT");$(win "$CU_ROOT/vendor/enikk")"
export PYTHONIOENCODING=utf-8
exec "$PY" -m cu_perceive "$@"
