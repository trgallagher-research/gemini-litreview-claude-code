"""
Configuration loading and saving utilities.
"""

import yaml
from pathlib import Path
from typing import Optional


def load_config(config_path: Path) -> dict:
    """Load project configuration from YAML file."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict, config_path: Path) -> None:
    """Save project configuration to YAML file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def get_source_count(config: dict) -> int:
    """Get the number of sources in the config."""
    return len(config.get("sources", {}))


def get_rq_ids(config: dict) -> list:
    """Get list of research question IDs."""
    return [rq["id"] for rq in config.get("research_questions", [])]
