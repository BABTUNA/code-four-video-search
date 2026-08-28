from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    with open(path) as handle:
        return yaml.safe_load(handle) or {}
