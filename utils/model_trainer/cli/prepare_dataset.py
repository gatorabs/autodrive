from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, "", "cli"):
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from services.dataset_preparation import (  # type: ignore
        DEFAULT_CLASS_NAMES,
        DEFAULT_DATASET_DIR,
        DEFAULT_OUTPUT_DIR,
        DEFAULT_VAL_RATIO,
        prepare_dataset,
    )
else:
    from ..services.dataset_preparation import (
        DEFAULT_CLASS_NAMES,
        DEFAULT_DATASET_DIR,
        DEFAULT_OUTPUT_DIR,
        DEFAULT_VAL_RATIO,
        prepare_dataset,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare one YOLO dataset and generate a data.yaml file."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--classes", nargs="*", default=DEFAULT_CLASS_NAMES)
    parser.add_argument("--class-ids", nargs="*", type=int)
    parser.add_argument("--val-ratio", type=float, default=DEFAULT_VAL_RATIO)
    parser.add_argument("--no-clean", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = prepare_dataset(
        dataset_dir=args.dataset,
        output_dir=args.output,
        class_names=args.classes,
        val_ratio=args.val_ratio,
        shuffle_seed=args.seed,
        clean_output=not args.no_clean,
        source_class_ids=args.class_ids or None,
    )
    print(
        f"Done | total={summary.total_pairs} | train={summary.train_pairs} | "
        f"val={summary.val_pairs} | data={summary.data_yaml}"
    )


if __name__ == "__main__":
    main()
