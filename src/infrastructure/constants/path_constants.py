from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

CONFIG_DIR = REPO_ROOT / "config"
RESOURCES_DIR = REPO_ROOT / "resources"
TEST_VIDEOS_DIR = RESOURCES_DIR / "test_videos"

CALIBRATION_FILE = CONFIG_DIR / "calibration_data.json"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"
DEFAULT_UI_PATH = CONFIG_DIR / "init_ui_defaults.json"
MODEL_REGISTRY_FILE = CONFIG_DIR / "model_registry.json"

__all__ = [
    "REPO_ROOT",
    "CONFIG_DIR",
    "RESOURCES_DIR",
    "TEST_VIDEOS_DIR",
    "CALIBRATION_FILE",
    "DEFAULTS_FILE",
    "DEFAULT_UI_PATH",
    "MODEL_REGISTRY_FILE",
]
