from __future__ import annotations

import os
from pathlib import Path
import yaml


def load_config(path: str | Path = 'configs/base.yaml') -> dict:
    path = os.environ.get('CAPSTONE_CONFIG', path)
    with Path(path).open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)
