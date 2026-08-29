#!/usr/bin/env bash
# Run cu-dsh from WSL (or Linux bash) on a Windows python.
# Zero hardcoded paths (M1): CU_ROOT derives from this script's location;
# the interpreter comes from CU_PYTHON or PATH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CU_ROOT="$(dirname "$SCRIPT_DIR")"

# 1. Interpreter: CU_PYTHON env wins; else probe python.exe on PATH.
#    Give CU_PYTHON a full path to a Windows python.exe, e.g.
#    CU_PYTHON=/mnt/c/Users/you/miniconda3/python.exe ./bin/cu-dsh.sh windows
PY="${CU_PYTHON:-}"
if [[ -z "$PY" ]]; then
  if command -v python.exe >/dev/null 2>&1; then
    PY="$(command -v python.exe)"
  else
    echo "cu-dsh: no Windows python found. Set CU_PYTHON to a full path of a Windows python.exe" >&2
    exit 2
  fi
fi

# 2. Env passing to a Windows process: WSL interop does NOT forward Linux env
#    vars unless they are listed in WSLENV. PYTHONPATH stays in Linux form
#    (colon-separated); the "/p" flag makes WSL convert it to Windows form
#    (semicolon-separated, /mnt/c -> C:\\) at spawn. Plain Linux pythons just
#    read the colon form directly, so one export serves both.
export PYTHONPATH="$CU_ROOT:$CU_ROOT/vendor/enikk"
export PYTHONIOENCODING=utf-8
export WSLENV="PYTHONPATH/p:PYTHONIOENCODING${WSLENV:+:$WSLENV}"
exec "$PY" -m cu_dsh "$@"
