#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

cd "${ROOT_DIR}"
export CAPSTONE_CONFIG="${ROOT_DIR}/configs/yeoksam_sumo.yaml"

"${PYTHON_BIN}" -m src.data.generate_yeoksam_synthetic_5min
"${PYTHON_BIN}" -m src.preprocessing.build_features
"${PYTHON_BIN}" -m src.dispatch.rule_based_dispatch
"${PYTHON_BIN}" -m src.analysis.summarize_phase1
"${PYTHON_BIN}" -m src.analysis.evaluate_dispatch
"${PYTHON_BIN}" -m src.visualization.plot_demand
"${PYTHON_BIN}" -m src.dispatch.export_yeoksam_to_sumo

echo "saved outputs under outputs/yeoksam_sumo"
echo "SUMO configs:"
echo "  module1_sumo/yeoksam_before.sumocfg"
echo "  module1_sumo/yeoksam_after.sumocfg"
