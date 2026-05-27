from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "config" / "model_registry.json"


@dataclass(frozen=True)
class TrainedModel:
    name: str
    path: Path
    classes: tuple[str, ...]
    updated_at: float


def relpath(path: Path, base: Path = REPO_ROOT) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _load_classes_from_yaml(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    names = payload.get("names") if isinstance(payload, dict) else None
    if isinstance(names, dict):
        parsed = []
        for key, value in names.items():
            try:
                parsed.append((int(key), str(value)))
            except (TypeError, ValueError):
                continue
        return tuple(value for _, value in sorted(parsed))
    if isinstance(names, list):
        return tuple(str(value) for value in names)
    return ()


def model_classes(model_path: Path) -> tuple[str, ...]:
    run_dir = model_path.parent.parent
    for candidate in (run_dir / "args.yaml", run_dir / "data.yaml", run_dir / "opt.yaml"):
        classes = _load_classes_from_yaml(candidate)
        if classes:
            return classes
    return ()


def discover_trained_models(root: Path | None = None) -> list[TrainedModel]:
    search_root = root or (Path(__file__).resolve().parent / "yolo_runs")
    if not search_root.exists():
        return []

    models = []
    for weight_path in search_root.rglob("weights/best.pt"):
        try:
            updated_at = weight_path.stat().st_mtime
        except OSError:
            updated_at = 0.0
        models.append(
            TrainedModel(
                name=weight_path.parent.parent.name,
                path=weight_path.resolve(),
                classes=model_classes(weight_path),
                updated_at=updated_at,
            )
        )
    return sorted(models, key=lambda item: item.updated_at, reverse=True)


def promote_model(model_path: str | Path, *, name: str | None = None) -> Path:
    path = Path(model_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")

    payload = {
        "name": name or path.parent.parent.name,
        "path": relpath(path),
        "classes": list(model_classes(path)),
        "promoted_at": datetime.now().isoformat(timespec="seconds"),
        "source": "utils/model_trainer",
    }

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return REGISTRY_PATH
