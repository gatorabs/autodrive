from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z_-]+", "-", value.strip())
    value = re.sub(r"-+", "-", value).strip("-_")
    return value or fallback


def normalise_names(raw_names: Any) -> tuple[str, ...]:
    if isinstance(raw_names, dict):
        parsed = []
        for key, value in raw_names.items():
            try:
                parsed.append((int(key), str(value)))
            except (TypeError, ValueError):
                continue
        return tuple(value for _, value in sorted(parsed))
    if isinstance(raw_names, list):
        return tuple(str(value) for value in raw_names)
    if isinstance(raw_names, (str, bytes)):
        return (str(raw_names),)
    return ()


def load_names_from_yaml(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    names = payload.get("names") if isinstance(payload, dict) else None
    return normalise_names(names)


def collect_label_class_ids(labels_dir: Path) -> tuple[int, ...]:
    ids: set[int] = set()
    for label_file in labels_dir.glob("*.txt"):
        try:
            lines = label_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                ids.add(int(float(parts[0])))
            except ValueError:
                continue
    return tuple(sorted(ids))
