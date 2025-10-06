"""Ferramentas para preparar datasets no formato YOLO."""

from __future__ import annotations

import argparse
import glob
import os
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
IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png", "*.bmp")


@dataclass
class DatasetSummary:
    """Resumo do particionamento do dataset."""

    total_pairs: int
    train_pairs: int
    val_pairs: int
    data_yaml: Path


def _gather_image_label_pairs(img_dir: Path, lab_dir: Path) -> list[tuple[Path, Path]]:
    """Retorna pares (imagem, label) existentes para o dataset."""

    pairs: list[tuple[Path, Path]] = []
    for pattern in IMAGE_EXTENSIONS:
        for img_path in sorted(img_dir.glob(pattern)):
            label_path = lab_dir / (img_path.stem + ".txt")
            if label_path.exists():
                pairs.append((img_path, label_path))
    return pairs


def _copy_pairs(pairs: Iterable[tuple[Path, Path]], dest_images: Path, dest_labels: Path) -> None:
    for img, lab in pairs:
        shutil.copy2(img, dest_images / img.name)
        shutil.copy2(lab, dest_labels / lab.name)


def prepare_dataset(dataset_dir: Path | str = DEFAULT_DATASET_DIR,
                    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
                    class_names: Sequence[str] = DEFAULT_CLASS_NAMES,
                    val_ratio: float = DEFAULT_VAL_RATIO,
                    shuffle_seed: int | None = 42,
                    clean_output: bool = True) -> DatasetSummary:
    """Organiza imagens/labels no formato esperado pelo YOLO.

    Parameters
    ----------
    dataset_dir:
        Pasta que contém ``images/`` e ``labels/`` com anotações no formato YOLO.
    output_dir:
        Pasta que receberá as divisões ``train`` e ``val``.
    class_names:
        Lista com os nomes das classes (ordem corresponde ao ID da classe).
    val_ratio:
        Proporção de dados reservada para validação.
    shuffle_seed:
        Semente usada para embaralhar os pares antes da divisão.
    clean_output:
        Se ``True`` remove o conteúdo existente do diretório de saída.

    Returns
    -------
    DatasetSummary
        Estrutura contendo estatísticas básicas e o caminho do ``data.yaml`` gerado.
    """

    dataset_dir = Path(dataset_dir)
    output_dir = Path(output_dir)

    img_dir = dataset_dir / "images"
    lab_dir = dataset_dir / "labels"

    if not img_dir.exists() or not lab_dir.exists():
        raise FileNotFoundError(
            f"Estrutura de dataset inválida em {dataset_dir}. "
            "É esperado encontrar pastas 'images/' e 'labels/'."
        )

    if clean_output and output_dir.exists():
        shutil.rmtree(output_dir)

    (output_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
    (output_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
    (output_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (output_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)

    pairs = _gather_image_label_pairs(img_dir, lab_dir)
    if shuffle_seed is not None:
        random.Random(shuffle_seed).shuffle(pairs)

    n_val = int(len(pairs) * val_ratio)
    val_pairs = pairs[:n_val]
    train_pairs = pairs[n_val:]

    _copy_pairs(train_pairs, output_dir / "images" / "train", output_dir / "labels" / "train")
    _copy_pairs(val_pairs, output_dir / "images" / "val", output_dir / "labels" / "val")

    data_yaml = output_dir / "data.yaml"
    data = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(class_names)},
    }

    with data_yaml.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    return DatasetSummary(
        total_pairs=len(pairs),
        train_pairs=len(train_pairs),
        val_pairs=len(val_pairs),
        data_yaml=data_yaml,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organiza datasets rotulados no formato YOLO e gera um data.yaml."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="Diretório contendo as pastas images/ e labels/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Diretório onde o conjunto preparado será salvo.",
    )
    parser.add_argument(
        "--classes",
        nargs="*",
        default=DEFAULT_CLASS_NAMES,
        help="Lista de nomes das classes (na ordem dos IDs).",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=DEFAULT_VAL_RATIO,
        help="Proporção reservada para validação (0-1).",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Não limpar o diretório de saída antes de copiar os arquivos.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente de aleatoriedade para embaralhar os pares.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = prepare_dataset(
        dataset_dir=args.dataset,
        output_dir=args.output,
        class_names=args.classes,
        val_ratio=args.val_ratio,
        shuffle_seed=args.seed,
        clean_output=not args.no_clean,
    )

    print("Feito!")
    print(
        "Total pares:",
        summary.total_pairs,
        "| train:",
        summary.train_pairs,
        "| val:",
        summary.val_pairs,
    )
    print(f"data.yaml: {summary.data_yaml}")
    print("Ajuste a lista de classes com --classes se tiver mais classes.")


if __name__ == "__main__":
    main()
