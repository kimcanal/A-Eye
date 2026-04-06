#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/legacy:${PYTHONPATH:-}"
"${PYTHON_BIN}" legacy/module1_simulation/minimal_simulation.py
