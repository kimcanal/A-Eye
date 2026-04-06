#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-safe}"

print_usage() {
  cat <<'EOF'
Usage: bash scripts/clean_generated_outputs.sh [safe|intermediate|all]

Modes:
  safe          Remove only scratch outputs (keeps visible final assets and datasets)
  intermediate  Remove reproducible generated outputs, keep final Unity presentation assets
  all           Remove all generated outputs plus generated local/public data artifacts
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
    "${ROOT_DIR}/outputs/local" \
    "${ROOT_DIR}/outputs/seoul_public" \
    "${ROOT_DIR}/outputs/module1/scratch" \
    "${ROOT_DIR}/data/seoul_public/raw"
}

remove_module1_debug_artifacts() {
  remove_path "${ROOT_DIR}/outputs/module1/play_toolbar_check.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_editor_after_click_play.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_editor_after_play.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_editor_before_play.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_editor_overview_restored.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_editor_restored_city.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_editor_window.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_toolbar_crop.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_window_capture.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_window_capture_live.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_window_capture_live2.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_window_capture_live3.png"
  remove_path "${ROOT_DIR}/outputs/module1/unity_window_small.png"
}

case "${MODE}" in
  safe)
    echo "Cleaning safe scratch outputs..."
    remove_path "${ROOT_DIR}/outputs/.DS_Store"
    remove_path "${ROOT_DIR}/outputs/module1/scratch"
    remove_module1_debug_artifacts
    ensure_layout
    ;;
  intermediate)
    echo "Cleaning intermediate generated outputs..."
    remove_path "${ROOT_DIR}/outputs/.DS_Store"
    remove_path "${ROOT_DIR}/outputs/local"
    remove_path "${ROOT_DIR}/outputs/seoul_public"
    remove_path "${ROOT_DIR}/outputs/module1/scratch"
    remove_path "${ROOT_DIR}/outputs/module1/frames"
    remove_path "${ROOT_DIR}/outputs/module1/module1_overview.png"
    remove_path "${ROOT_DIR}/outputs/module1/module1_simulation.gif"
    remove_path "${ROOT_DIR}/outputs/module1/module1_simulation_log.json"
    remove_path "${ROOT_DIR}/outputs/module1/module1_summary.json"
    remove_module1_debug_artifacts
    ensure_layout
    ;;
  all)
    echo "Cleaning all generated outputs and generated data artifacts..."
    remove_path "${ROOT_DIR}/outputs"
    remove_path "${ROOT_DIR}/data/local_taxi_calls.csv"
    remove_path "${ROOT_DIR}/data/seoul_public/raw"
    remove_path "${ROOT_DIR}/data/seoul_public/dong_master.csv"
    remove_path "${ROOT_DIR}/data/seoul_public/transit_demand_long.csv"
    remove_path "${ROOT_DIR}/data/seoul_public/zone_lookup.csv"
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
