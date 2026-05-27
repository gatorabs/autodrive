"""YOLO dataset preparation helpers used by the trainer UI and CLI tools."""

from __future__ import annotations

import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml


DEFAULT_DATASET_DIR = Path("dataset")
DEFAULT_OUTPUT_DIR = Path("yolo_data")
DEFAULT_VAL_RATIO = 0.2
DEFAULT_CLASS_NAMES = ["objeto"]
IMAGE_PATTERNS = ("*.jpg", "*.jpeg", "*.png", "*.bmp")


@dataclass(frozen=True)
class DatasetSummary:
    total_pairs: int
    train_pairs: int
    val_pairs: int
    data_yaml: Path


def gather_image_label_pairs(images_dir: Path, labels_dir: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for pattern in IMAGE_PATTERNS:
        for image_path in sorted(images_dir.glob(pattern)):
            label_path = labels_dir / f"{image_path.stem}.txt"
            if label_path.exists():
                pairs.append((image_path, label_path))
    return pairs


def prepare_dataset(
    dataset_dir: Path | str = DEFAULT_DATASET_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    class_names: Sequence[str] = DEFAULT_CLASS_NAMES,
    val_ratio: float = DEFAULT_VAL_RATIO,
    shuffle_seed: int | None = 42,
    clean_output: bool = True,
    source_class_ids: Sequence[int] | None = None,
) -> DatasetSummary:
    dataset_dir = Path(dataset_dir)
    return prepare_dataset_from_parts(
        dataset_dirs=[dataset_dir],
        output_dir=output_dir,
        class_names=class_names,
        val_ratio=val_ratio,
        shuffle_seed=shuffle_seed,
        clean_output=clean_output,
        source_class_ids=source_class_ids,
    )


def prepare_dataset_from_parts(
    dataset_dirs: Sequence[Path | str],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    class_names: Sequence[str] = DEFAULT_CLASS_NAMES,
    val_ratio: float = DEFAULT_VAL_RATIO,
    shuffle_seed: int | None = 42,
    clean_output: bool = True,
    source_class_ids: Sequence[int] | None = None,
) -> DatasetSummary:
    if not dataset_dirs:
        raise ValueError("At least one dataset directory is required.")
    if len(class_names) != len(dataset_dirs):
        raise ValueError("class_names must have the same length as dataset_dirs.")

    source_ids = _resolve_source_ids(dataset_dirs, class_names, source_class_ids)
    output_dir = Path(output_dir)
    if clean_output and output_dir.exists():
        shutil.rmtree(output_dir)

    train_images = output_dir / "images" / "train"
    val_images = output_dir / "images" / "val"
    train_labels = output_dir / "labels" / "train"
    val_labels = output_dir / "labels" / "val"
    for directory in (train_images, val_images, train_labels, val_labels):
        directory.mkdir(parents=True, exist_ok=True)

    indexed_pairs = _collect_indexed_pairs(dataset_dirs)
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(indexed_pairs)

    split_at = int(len(indexed_pairs) * val_ratio)
    val_pairs = indexed_pairs[:split_at]
    train_pairs = indexed_pairs[split_at:]

    _copy_indexed_pairs(train_pairs, train_images, train_labels, source_ids)
    _copy_indexed_pairs(val_pairs, val_images, val_labels, source_ids)
    data_yaml = _write_data_yaml(output_dir, class_names)

    return DatasetSummary(
        total_pairs=len(indexed_pairs),
        train_pairs=len(train_pairs),
        val_pairs=len(val_pairs),
        data_yaml=data_yaml,
    )


def _resolve_source_ids(
    dataset_dirs: Sequence[Path | str],
    class_names: Sequence[str],
    source_class_ids: Sequence[int] | None,
) -> list[int]:
    if source_class_ids is None:
        return [0 for _ in dataset_dirs]
    if len(source_class_ids) != len(class_names):
        raise ValueError("source_class_ids must have the same length as class_names.")
    return [int(value) for value in source_class_ids]


def _collect_indexed_pairs(dataset_dirs: Sequence[Path | str]) -> list[tuple[int, tuple[Path, Path]]]:
    indexed_pairs: list[tuple[int, tuple[Path, Path]]] = []
    for source_index, raw_dir in enumerate(dataset_dirs):
        dataset_dir = Path(raw_dir)
        images_dir = dataset_dir / "images"
        labels_dir = dataset_dir / "labels"
        if not images_dir.exists() or not labels_dir.exists():
            raise FileNotFoundError(
                f"Invalid dataset structure in {dataset_dir}. Expected images/ and labels/."
            )
        for pair in gather_image_label_pairs(images_dir, labels_dir):
            indexed_pairs.append((source_index, pair))
    return indexed_pairs


def _copy_indexed_pairs(
    pairs: Iterable[tuple[int, tuple[Path, Path]]],
    dest_images: Path,
    dest_labels: Path,
    source_ids: Sequence[int],
) -> None:
    for source_index, (image_path, label_path) in pairs:
        prefix = f"{source_index:02d}_"
        shutil.copy2(image_path, dest_images / f"{prefix}{image_path.name}")
        _rewrite_label_file(
            label_path,
            dest_labels / f"{prefix}{label_path.name}",
            class_mapping={source_ids[source_index]: source_index},
        )


def _rewrite_label_file(src: Path, dest: Path, class_mapping: dict[int, int]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    rewritten: list[str] = []
    for raw_line in src.read_text(encoding="utf-8").splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        try:
            original_id = int(float(parts[0]))
        except ValueError as exc:
            raise ValueError(f"Invalid class id in {src}: {parts[0]}") from exc
        if original_id not in class_mapping:
            raise ValueError(f"Class id {original_id} from {src} is not present in class_ids.")
        parts[0] = str(class_mapping[original_id])
        rewritten.append(" ".join(parts))
    dest.write_text(("\n".join(rewritten) + "\n") if rewritten else "", encoding="utf-8")


def _write_data_yaml(output_dir: Path, class_names: Sequence[str]) -> Path:
    data_yaml = output_dir / "data.yaml"
    payload = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {index: name for index, name in enumerate(class_names)},
    }
    data_yaml.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return data_yaml
