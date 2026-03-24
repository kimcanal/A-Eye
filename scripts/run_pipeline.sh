#!/usr/bin/env bash
set -euo pipefail

python -m src.preprocessing.build_features
python -m src.prediction.train_baseline
python -m src.dispatch.rule_based_dispatch
python -m src.visualization.plot_demand
