from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .metadata_service import IMAGE_EXTENSIONS, collect_label_class_ids, load_names_from_yaml


@dataclass(frozen=True)
class DatasetInventory:
    path: Path
    class_name: str
    class_ids: tuple[int, ...]
    image_count: int
    label_count: int
    paired_count: int
    images_without_labels: int
    labels_without_images: int

    @property
    def is_valid(self) -> bool:
        return self.paired_count > 0 and self.images_without_labels == 0


def inspect_dataset(dataset_dir: str | Path) -> DatasetInventory | None:
    path = Path(dataset_dir)
    images_dir = path / "images"
    labels_dir = path / "labels"
    if not images_dir.is_dir() or not labels_dir.is_dir():
        return None

    image_stems = {
        item.stem
        for item in images_dir.iterdir()
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
    }
    label_stems = {item.stem for item in labels_dir.glob("*.txt") if item.is_file()}
    class_ids = collect_label_class_ids(labels_dir)
    names = load_names_from_yaml(path / "data.yaml")

    if class_ids and names and class_ids[0] < len(names):
        class_name = names[class_ids[0]]
    elif names:
        class_name = names[0]
    else:
        class_name = path.name

    return DatasetInventory(
        path=path.resolve(),
        class_name=class_name,
        class_ids=class_ids or (0,),
        image_count=len(image_stems),
        label_count=len(label_stems),
        paired_count=len(image_stems & label_stems),
        images_without_labels=len(image_stems - label_stems),
        labels_without_images=len(label_stems - image_stems),
    )


def discover_datasets(root: str | Path) -> list[DatasetInventory]:
    base = Path(root)
    if not base.exists():
        return []

    candidates: list[Path] = []
    if (base / "images").is_dir() and (base / "labels").is_dir():
        candidates.append(base)
    candidates.extend(
        child
        for child in sorted(base.iterdir())
        if child.is_dir() and (child / "images").is_dir() and (child / "labels").is_dir()
    )

    inventories = []
    for candidate in candidates:
        inventory = inspect_dataset(candidate)
        if inventory is not None:
            inventories.append(inventory)
    return inventories
