from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL_REGISTRY_PATH = Path("config/model_registry.json")


@dataclass(frozen=True)
class ActiveModel:
    name: str
    path: Path
    classes: tuple[str, ...] = ()
    promoted_at: str = ""
    source: str = ""


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve_model_path(raw_path: str | Path, *, base_dir: Path | None = None) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return ((base_dir or get_repo_root()) / path).resolve()


def load_active_model(
    registry_path: str | Path = DEFAULT_MODEL_REGISTRY_PATH,
    *,
    base_dir: Path | None = None,
) -> ActiveModel | None:
    root = base_dir or get_repo_root()
    resolved_registry = resolve_model_path(registry_path, base_dir=root)
    if not resolved_registry.exists():
        return None

    try:
        payload = json.loads(resolved_registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    raw_model_path = payload.get("path") or payload.get("model_path")
    if not raw_model_path:
        return None

    model_path = resolve_model_path(str(raw_model_path), base_dir=root)
    if not model_path.exists() or not model_path.is_file():
        return None

    raw_classes: Any = payload.get("classes", ())
    if isinstance(raw_classes, dict):
        classes = tuple(str(value) for _, value in sorted(raw_classes.items()))
    elif isinstance(raw_classes, (list, tuple)):
        classes = tuple(str(value) for value in raw_classes)
    else:
        classes = ()

    return ActiveModel(
        name=str(payload.get("name") or model_path.stem),
        path=model_path,
        classes=classes,
        promoted_at=str(payload.get("promoted_at") or ""),
        source=str(payload.get("source") or ""),
    )
