"""Orquestra o preparo do dataset e o treinamento de múltiplos modelos YOLO."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml

if __package__ in (None, ""):
    from _train_model import DatasetSummary, prepare_dataset, prepare_dataset_from_parts  # type: ignore
else:  # pragma: no cover - caminho utilizado quando importado como pacote
    from ._train_model import DatasetSummary, prepare_dataset, prepare_dataset_from_parts


DEFAULT_BASE_MODEL = "yolov8n.pt"


class TrainingError(RuntimeError):
    """Erro levantado quando alguma etapa do treinamento falha."""


@dataclass
class TrainingConfig:
    """Configuração de treinamento carregada do arquivo YAML."""

    name: str
    dataset: Path | None
    classes: Sequence[str]
    output: Path
    val_ratio: float = 0.2
    class_ids: Sequence[int] | None = None
    train_args: Dict[str, Any] = field(default_factory=dict)
    dataset_parts: Sequence[Path] = ()

    def ensure_defaults(self) -> None:
        self.train_args.setdefault("model", DEFAULT_BASE_MODEL)


@dataclass
class DiscoveredDataset:
    """Informações básicas sobre um dataset encontrado automaticamente."""

    path: Path
    class_names: List[str]
    class_ids: List[int]

    @property
    def display_name(self) -> str:
        if self.class_names:
            return self.class_names[0]
        return self.path.name


def _load_yaml_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("Arquivo de configuração inválido: raiz deve ser um objeto.")
    return data


def _parse_training_configs(config_data: dict[str, Any], base_dir: Path) -> List[TrainingConfig]:
    models = config_data.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("Arquivo de configuração deve conter uma lista 'models'.")

    parsed: List[TrainingConfig] = []
    for entry in models:
        if not isinstance(entry, dict):
            raise ValueError("Cada item em 'models' deve ser um objeto.")

        try:
            name = entry["name"]
            dataset_entry = entry["dataset"]
            classes = entry["classes"]
        except KeyError as exc:
            raise ValueError(f"Campo obrigatório ausente na configuração: {exc}") from exc

        if not isinstance(name, str) or not name:
            raise ValueError("Campo 'name' deve ser uma string não vazia.")
        if not isinstance(classes, Iterable) or isinstance(classes, (str, bytes)):
            raise ValueError("Campo 'classes' deve ser uma lista de strings.")

        dataset_path: Path | None
        dataset_parts: List[Path]

        if isinstance(dataset_entry, Iterable) and not isinstance(dataset_entry, (str, bytes, Path)):
            dataset_path = None
            dataset_parts = []
            for item in dataset_entry:
                if not isinstance(item, (str, bytes, Path)):
                    raise ValueError(
                        "Ao utilizar uma lista em 'dataset', informe apenas caminhos válidos."
                    )
                path_obj = Path(item)
                resolved = (base_dir / path_obj).resolve() if not path_obj.is_absolute() else path_obj
                dataset_parts.append(resolved)
            if not dataset_parts:
                raise ValueError("Lista 'dataset' não pode ser vazia.")
        else:
            path_obj = Path(dataset_entry)
            dataset_path = (
                (base_dir / path_obj).resolve() if not path_obj.is_absolute() else path_obj
            )
            dataset_parts = []

        class_ids = entry.get("class_ids")
        parsed_class_ids: List[int] | None
        if class_ids is None:
            parsed_class_ids = None
        else:
            if not isinstance(class_ids, Iterable) or isinstance(class_ids, (str, bytes)):
                raise ValueError("Campo 'class_ids' deve ser uma lista de inteiros.")
            parsed_class_ids = [int(value) for value in class_ids]

        output = entry.get("output")
        output_path = Path(output) if output else Path("yolo_data") / name

        val_ratio = float(entry.get("val_ratio", 0.2))
        train_args = entry.get("train", {})
        if not isinstance(train_args, dict):
            raise ValueError("Campo 'train' deve ser um objeto com argumentos do YOLO CLI.")

        config = TrainingConfig(
            name=name,
            dataset=dataset_path,
            classes=list(classes),
            class_ids=parsed_class_ids,
            output=(base_dir / output_path).resolve() if not output_path.is_absolute() else output_path,
            val_ratio=val_ratio,
            train_args=train_args.copy(),
            dataset_parts=dataset_parts,
        )
        config.ensure_defaults()
        parsed.append(config)

    return parsed


def _build_train_command(train_args: Dict[str, Any], data_yaml: Path) -> List[str]:
    args = ["yolo", "detect", "train"]

    effective_args = train_args.copy()
    effective_args.setdefault("data", str(data_yaml))

    for key, value in effective_args.items():
        args.append(f"{key}={value}")

    return args


def _run_command(command: Sequence[str], dry_run: bool) -> None:
    if dry_run:
        print("[dry-run]", " ".join(command))
        return

    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise TrainingError(
            f"Comando {' '.join(command)} finalizou com código {result.returncode}."
        )


def _slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z_-]+", "-", value.strip())
    value = re.sub(r"-+", "-", value).strip("-_")
    return value or fallback


def _relpath_for_config(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        pass

    try:
        return os.path.relpath(path, base)
    except (ValueError, OSError):
        return str(path.resolve())


def _collect_label_ids(labels_dir: Path) -> List[int]:
    ids: set[int] = set()
    for label_file in labels_dir.glob("*.txt"):
        try:
            with label_file.open("r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except OSError:
            continue

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if not parts:
                continue
            try:
                class_id = int(float(parts[0]))
            except ValueError:
                continue
            ids.add(class_id)
    return sorted(ids)


def _load_names_from_yaml(dataset_dir: Path) -> List[str]:
    yaml_path = dataset_dir / "data.yaml"
    if not yaml_path.exists():
        return []

    try:
        with yaml_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except OSError:
        return []

    names_field = data.get("names") if isinstance(data, dict) else None
    if isinstance(names_field, dict):
        items = []
        for key, value in names_field.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                continue
            items.append((idx, str(value)))
        return [name for _, name in sorted(items, key=lambda item: item[0])]
    if isinstance(names_field, list):
        return [str(name) for name in names_field]
    if isinstance(names_field, (str, bytes)):
        return [str(names_field)]
    return []


def _discover_datasets_in_root(root: Path) -> List[DiscoveredDataset]:
    datasets: List[DiscoveredDataset] = []
    if not root.exists() or not root.is_dir():
        return datasets

    candidates: List[Path] = []
    if (root / "images").is_dir() and (root / "labels").is_dir():
        candidates.append(root)

    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "images").is_dir() and (child / "labels").is_dir():
            candidates.append(child)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)

        label_ids = _collect_label_ids(candidate / "labels")
        raw_names = _load_names_from_yaml(candidate)

        if not label_ids and raw_names:
            label_ids = list(range(len(raw_names)))
        elif not label_ids:
            label_ids = [0]

        class_names: List[str] = []
        for cid in label_ids:
            if cid < len(raw_names):
                class_names.append(raw_names[cid])
            else:
                class_names.append(f"classe_{cid:02d}")

        if not class_names:
            class_names = [candidate.name]

        datasets.append(
            DiscoveredDataset(
                path=resolved,
                class_names=class_names,
                class_ids=label_ids,
            )
        )

    return datasets


def _auto_generate_config(base_dir: Path) -> Path | None:
    script_dir = Path(__file__).resolve().parent
    candidate_roots = [
        base_dir / "dataset",
        base_dir / "datasets",
        script_dir / "dataset",
        script_dir / "datasets",
    ]

    discovered: List[DiscoveredDataset] = []
    for root in candidate_roots:
        discovered.extend(_discover_datasets_in_root(root))

    # Garantir unicidade por caminho resolvido
    unique: dict[Path, DiscoveredDataset] = {}
    for ds in discovered:
        unique.setdefault(ds.path, ds)

    datasets = sorted(unique.values(), key=lambda ds: ds.path)
    if not datasets:
        return None

    config_dir = script_dir
    config_path = config_dir / "training_config.auto.yaml"

    models: List[dict[str, Any]] = []
    for ds in datasets:
        dataset_ref = _relpath_for_config(ds.path, config_dir)
        model_name = _slugify(ds.display_name, ds.path.name)
        models.append(
            {
                "name": model_name,
                "dataset": dataset_ref,
                "classes": ds.class_names,
                "class_ids": ds.class_ids,
                "output": f"yolo_runs/{model_name}",
                "val_ratio": 0.2,
                "train": {},
            }
        )

    single_class = [
        ds for ds in datasets if len(ds.class_ids) == 1 and len(ds.class_names) == 1
    ]
    single_class.sort(key=lambda ds: ds.class_ids[0])
    if len(single_class) > 1:
        combined_name = _slugify("todos_objetos", "modelo_agregado")
        models.append(
            {
                "name": combined_name,
                "dataset": [
                    _relpath_for_config(ds.path, config_dir) for ds in single_class
                ],
                "classes": [ds.class_names[0] for ds in single_class],
                "class_ids": [ds.class_ids[0] for ds in single_class],
                "output": f"yolo_runs/{combined_name}",
                "val_ratio": 0.2,
                "train": {},
            }
        )

    common_base = Path(os.path.commonpath([str(ds.path.parent) for ds in datasets]))

    config_payload = {
        "auto_generated": True,
        "base_dataset": _relpath_for_config(common_base, config_dir),
        "models": models,
    }

    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config_payload, fh, allow_unicode=True, sort_keys=False)

    print(
        "Arquivo de configuração gerado automaticamente em",
        config_path,
    )

    return config_path


def run_pipeline(configs: Sequence[TrainingConfig], *, dry_run: bool = False, skip_train: bool = False) -> None:
    for cfg in configs:
        print(f"\n=== Modelo: {cfg.name} ===")
        print(f"Dataset: {cfg.dataset}")
        print(f"Saída: {cfg.output}")

        if cfg.dataset_parts:
            summary: DatasetSummary = prepare_dataset_from_parts(
                dataset_dirs=cfg.dataset_parts,
                output_dir=cfg.output,
                class_names=cfg.classes,
                val_ratio=cfg.val_ratio,
                source_class_ids=cfg.class_ids,
            )
        elif cfg.dataset is not None:
            summary = prepare_dataset(
                dataset_dir=cfg.dataset,
                output_dir=cfg.output,
                class_names=cfg.classes,
                val_ratio=cfg.val_ratio,
                source_class_ids=cfg.class_ids,
            )
        else:
            raise ValueError(
                "Configuração inválida: informe um caminho em 'dataset' ou uma lista de diretórios."
            )

        print(
            f"Dataset preparado | total: {summary.total_pairs} | "
            f"train: {summary.train_pairs} | val: {summary.val_pairs}"
        )
        print(f"data.yaml: {summary.data_yaml}")

        if skip_train:
            print("Treinamento ignorado (--skip-train).")
            continue

        command = _build_train_command(cfg.train_args, summary.data_yaml)
        print("Executando:", " ".join(command))
        _run_command(command, dry_run=dry_run)


def _default_config_candidates(base: Path) -> List[Path]:
    """Retorna caminhos candidatos para o arquivo de configuração padrão."""

    cwd = base.resolve()
    script_dir = Path(__file__).resolve().parent

    candidates = [
        cwd / "training_config.yaml",
        cwd / "training_config.yml",
        cwd / "training_config.auto.yaml",
        cwd / "training_config.auto.yml",
        script_dir / "training_config.yaml",
        script_dir / "training_config.yml",
        script_dir / "training_config.auto.yaml",
        script_dir / "training_config.auto.yml",
    ]

    # Garantir unicidade preservando a ordem
    seen = set()
    unique_candidates: List[Path] = []
    for candidate in candidates:
        if candidate not in seen:
            unique_candidates.append(candidate)
            seen.add(candidate)

    return unique_candidates


def _resolve_config_path(provided: Path | None) -> Path:
    if provided is not None:
        return provided

    for candidate in _default_config_candidates(Path.cwd()):
        if candidate.exists():
            return candidate

    auto_generated = _auto_generate_config(Path.cwd())
    if auto_generated is not None and auto_generated.exists():
        return auto_generated

    raise SystemExit(
        "Nenhum arquivo de configuração encontrado. Informe --config PATH ou crie "
        "um training_config.yaml na pasta atual ou em utils/model_trainer/."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepara datasets e dispara o treinamento de múltiplos modelos YOLO."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Arquivo YAML com as configurações dos modelos."
             " Se omitido, procura por training_config.yaml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas imprime os comandos do YOLO sem executá-los.",
    )
    parser.add_argument(
        "--skip-train",
        action="store_true",
        help="Prepara os datasets mas não executa o treinamento.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config_path = _resolve_config_path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Arquivo de configuração não encontrado: {config_path}")
    config_path = config_path.resolve()
    config_data = _load_yaml_config(config_path)
    configs = _parse_training_configs(config_data, base_dir=config_path.parent)
    run_pipeline(configs, dry_run=args.dry_run, skip_train=args.skip_train)


if __name__ == "__main__":
    main()
