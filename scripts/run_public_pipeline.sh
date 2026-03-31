#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

cd "${ROOT_DIR}"

"${PYTHON_BIN}" -m src.data.fetch_seoul_transit_demand
"${PYTHON_BIN}" -m src.data.transform_seoul_transit_demand

export CAPSTONE_CONFIG="${ROOT_DIR}/configs/seoul_public.yaml"
"${PYTHON_BIN}" -m src.preprocessing.build_features
"${PYTHON_BIN}" -m src.prediction.train_baseline
"${PYTHON_BIN}" -m src.dispatch.rule_based_dispatch
"${PYTHON_BIN}" -m src.visualization.plot_demand
"${PYTHON_BIN}" -m src.analysis.summarize_phase1
"${PYTHON_BIN}" -m src.analysis.evaluate_dispatch

echo "saved outputs under outputs/seoul_public"
