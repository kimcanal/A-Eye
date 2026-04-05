#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Cleaning generated files under outputs/ and transient public-data artifacts..."

rm -rf "${ROOT_DIR}/outputs"
rm -f "${ROOT_DIR}/data/local_taxi_calls.csv"
rm -rf "${ROOT_DIR}/data/seoul_public"

mkdir -p "${ROOT_DIR}/outputs"

echo "Done."
