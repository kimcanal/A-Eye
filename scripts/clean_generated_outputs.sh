#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-safe}"

print_usage() {
  cat <<'EOF'
Usage: bash scripts/clean_generated_outputs.sh [safe|intermediate|all]

Modes:
  safe          Remove only scratch outputs for the active Yeoksam SUMO path
  intermediate  Remove reproducible generated outputs for the active Yeoksam SUMO path
  all           Remove all generated active outputs plus the generated Yeoksam dataset
EOF
}

remove_path() {
  local path="$1"
  if [[ -e "${path}" ]]; then
    rm -rf "${path}"
  fi
}

ensure_layout() {
  mkdir -p \
    "${ROOT_DIR}/outputs/yeoksam_sumo"
}

case "${MODE}" in
  safe)
    echo "Cleaning safe scratch outputs..."
    remove_path "${ROOT_DIR}/outputs/.DS_Store"
    ensure_layout
    ;;
  intermediate)
    echo "Cleaning intermediate generated outputs..."
    remove_path "${ROOT_DIR}/outputs/.DS_Store"
    remove_path "${ROOT_DIR}/outputs/yeoksam_sumo"
    ensure_layout
    ;;
  all)
    echo "Cleaning all generated active outputs and generated Yeoksam data..."
    remove_path "${ROOT_DIR}/outputs"
    remove_path "${ROOT_DIR}/data/yeoksam_synthetic_5min.csv"
    ensure_layout
    ;;
  -h|--help)
    print_usage
    exit 0
    ;;
  *)
    print_usage >&2
    exit 1
    ;;
esac

echo "Done."
