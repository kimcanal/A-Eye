#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUMO_ROOT="${SUMO_ROOT:-/Users/kenny31/Library/Frameworks/EclipseSUMO.framework/Versions/Current/EclipseSUMO}"
SUMO_GUI_BIN="${SUMO_GUI_BIN:-${SUMO_ROOT}/bin/sumo-gui}"
SUMO_CFG="${1:-${ROOT_DIR}/module1_sumo/yeoksam_after.sumocfg}"

if [[ ! -x "${SUMO_GUI_BIN}" ]]; then
  echo "sumo-gui not found: ${SUMO_GUI_BIN}" >&2
  exit 1
fi

if [[ ! -f "${SUMO_CFG}" ]]; then
  echo "sumo config not found: ${SUMO_CFG}" >&2
  exit 1
fi

export SUMO_HOME="${SUMO_HOME:-${SUMO_ROOT}/share/sumo}"

cd "$(dirname "${SUMO_CFG}")"
exec "${SUMO_GUI_BIN}" -c "$(basename "${SUMO_CFG}")"
