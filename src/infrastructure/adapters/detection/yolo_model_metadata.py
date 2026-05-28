from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def normalise_names_payload(raw_names: Any) -> Dict[int, str]:
    """Converte diferentes representações de nomes do YOLO em um dicionário padronizado."""

    if isinstance(raw_names, dict):
        normalised: Dict[int, str] = {}
        for key, value in raw_names.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                continue
            normalised[idx] = str(value)
        return normalised

    if isinstance(raw_names, (list, tuple)):
        return {idx: str(name) for idx, name in enumerate(raw_names)}

    return {}


def load_names_from_metadata(model_path: Path) -> Dict[int, str]:
    """Tenta recuperar os nomes das classes a partir dos artefatos do treinamento."""

    run_dir = model_path.parent.parent
    candidates = [
        run_dir / "args.yaml",
        run_dir / "opt.yaml",
        run_dir / "data.yaml",
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue

        try:
            with candidate.open("r", encoding="utf-8") as fh:
                payload = yaml.safe_load(fh)
        except Exception:
            continue

        if isinstance(payload, dict):
            for key in ("names", "class_names"):
                if key in payload:
                    names = normalise_names_payload(payload[key])
                    if names:
                        return names

    return {}
