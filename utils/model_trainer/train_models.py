"""Orquestra o preparo do dataset e o treinamento de múltiplos modelos YOLO."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml

if __package__ in (None, ""):
    from _train_model import DatasetSummary, prepare_dataset  # type: ignore
else:  # pragma: no cover - caminho utilizado quando importado como pacote
    from ._train_model import DatasetSummary, prepare_dataset


DEFAULT_BASE_MODEL = "yolov8n.pt"


class TrainingError(RuntimeError):
    """Erro levantado quando alguma etapa do treinamento falha."""


@dataclass
class TrainingConfig:
    """Configuração de treinamento carregada do arquivo YAML."""

    name: str
    dataset: Path
    classes: Sequence[str]
    output: Path
    val_ratio: float = 0.2
    train_args: Dict[str, Any] = field(default_factory=dict)

    def ensure_defaults(self) -> None:
        self.train_args.setdefault("model", DEFAULT_BASE_MODEL)


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
            dataset = Path(entry["dataset"])
            classes = entry["classes"]
        except KeyError as exc:
            raise ValueError(f"Campo obrigatório ausente na configuração: {exc}") from exc

        if not isinstance(name, str) or not name:
            raise ValueError("Campo 'name' deve ser uma string não vazia.")
        if not isinstance(classes, Iterable) or isinstance(classes, (str, bytes)):
            raise ValueError("Campo 'classes' deve ser uma lista de strings.")

        output = entry.get("output")
        output_path = Path(output) if output else Path("yolo_data") / name

        val_ratio = float(entry.get("val_ratio", 0.2))
        train_args = entry.get("train", {})
        if not isinstance(train_args, dict):
            raise ValueError("Campo 'train' deve ser um objeto com argumentos do YOLO CLI.")

        config = TrainingConfig(
            name=name,
            dataset=(base_dir / dataset).resolve() if not dataset.is_absolute() else dataset,
            classes=list(classes),
            output=(base_dir / output_path).resolve() if not output_path.is_absolute() else output_path,
            val_ratio=val_ratio,
            train_args=train_args.copy(),
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


def run_pipeline(configs: Sequence[TrainingConfig], *, dry_run: bool = False, skip_train: bool = False) -> None:
    for cfg in configs:
        print(f"\n=== Modelo: {cfg.name} ===")
        print(f"Dataset: {cfg.dataset}")
        print(f"Saída: {cfg.output}")

        summary: DatasetSummary = prepare_dataset(
            dataset_dir=cfg.dataset,
            output_dir=cfg.output,
            class_names=cfg.classes,
            val_ratio=cfg.val_ratio,
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
