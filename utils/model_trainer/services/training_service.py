from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

if __package__ in (None, ""):
    from dataset_preparation import DatasetSummary, prepare_dataset_from_parts  # type: ignore
    from dataset_service import DatasetInventory  # type: ignore
else:
    from .dataset_preparation import DatasetSummary, prepare_dataset_from_parts
    from .dataset_service import DatasetInventory


DEFAULT_BASE_MODEL = "yolov8n.pt"


@dataclass(frozen=True)
class TrainingRequest:
    datasets: Sequence[DatasetInventory]
    name: str = "todos_objetos"
    base_model: str = DEFAULT_BASE_MODEL
    epochs: int = 50
    image_size: int = 640
    batch: int = 8
    device: str = "auto"
    val_ratio: float = 0.2
    seed: int = 42
    dry_run: bool = False
    prepare_only: bool = False


@dataclass(frozen=True)
class TrainingResult:
    prepared_dataset: DatasetSummary
    run_dir: Path
    best_weights: Path


def _timestamped_name(name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in name)
    return f"{safe_name}_{stamp}"


def build_training_command(request: TrainingRequest, data_yaml: Path, run_dir: Path) -> list[str]:
    command = [
        "yolo",
        "detect",
        "train",
        f"model={request.base_model}",
        f"data={data_yaml}",
        f"project={run_dir.parent}",
        f"name={run_dir.name}",
        "exist_ok=False",
        f"epochs={max(1, int(request.epochs))}",
        f"imgsz={max(64, int(request.image_size))}",
        f"batch={max(1, int(request.batch))}",
        f"seed={int(request.seed)}",
    ]
    if request.device and request.device != "auto":
        command.append(f"device={request.device}")
    return command


def run_training(
    request: TrainingRequest,
    *,
    output_root: Path | None = None,
    log: Callable[[str], None] | None = None,
) -> TrainingResult:
    if not request.datasets:
        raise ValueError("Select at least one dataset before training.")

    emit = log or (lambda message: None)
    trainer_dir = Path(__file__).resolve().parents[1]
    runs_root = output_root or trainer_dir / "yolo_runs"
    run_name = _timestamped_name(request.name)
    prepared_dir = runs_root / "_prepared" / run_name
    run_dir = runs_root / run_name

    emit(f"Preparing composed dataset: {run_name}")
    summary = prepare_dataset_from_parts(
        dataset_dirs=[item.path for item in request.datasets],
        output_dir=prepared_dir,
        class_names=[item.class_name for item in request.datasets],
        val_ratio=request.val_ratio,
        shuffle_seed=request.seed,
        source_class_ids=[item.class_ids[0] for item in request.datasets],
    )
    emit(
        f"Dataset ready: total={summary.total_pairs}, "
        f"train={summary.train_pairs}, val={summary.val_pairs}"
    )

    best_weights = run_dir / "weights" / "best.pt"
    command = build_training_command(request, summary.data_yaml, run_dir)
    emit("Command: " + " ".join(str(item) for item in command))

    if request.dry_run or request.prepare_only:
        return TrainingResult(summary, run_dir, best_weights)

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    for line in process.stdout:
        emit(line.rstrip())

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"YOLO training failed with exit code {return_code}.")

    if not best_weights.exists():
        raise FileNotFoundError(f"Training finished, but best weights were not found: {best_weights}")

    emit(f"Best weights: {best_weights}")
    return TrainingResult(summary, run_dir, best_weights)
