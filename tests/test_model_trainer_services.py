import tempfile
import unittest
from pathlib import Path

from utils.model_trainer.services.dataset_service import discover_datasets
from utils.model_trainer.services.training_service import TrainingRequest, run_training


def create_dataset(root: Path, name: str, class_id: int) -> Path:
    dataset = root / name
    images = dataset / "images"
    labels = dataset / "labels"
    images.mkdir(parents=True)
    labels.mkdir()
    (images / f"{name}.jpg").write_bytes(b"fake image")
    (labels / f"{name}.txt").write_text(
        f"{class_id} 0.500000 0.500000 0.200000 0.200000\n",
        encoding="utf-8",
    )
    (dataset / "data.yaml").write_text(
        f"path: {dataset}\ntrain: images\nval: images\nnames:\n  {class_id}: {name}\n",
        encoding="utf-8",
    )
    return dataset


class ModelTrainerServicesTest(unittest.TestCase):
    def test_discovers_dataset_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_dataset(root, "PLACA_PARE", 0)

            datasets = discover_datasets(root)

        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0].class_name, "PLACA_PARE")
        self.assertEqual(datasets[0].paired_count, 1)
        self.assertTrue(datasets[0].is_valid)

    def test_prepare_only_builds_composed_dataset_without_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_dataset(root, "PLACA_PARE", 0)
            create_dataset(root, "PLACA_LOMBADA", 1)
            datasets = discover_datasets(root)

            result = run_training(
                TrainingRequest(datasets=datasets, prepare_only=True),
                output_root=root / "runs",
            )

            data_yaml = result.prepared_dataset.data_yaml
            payload = data_yaml.read_text(encoding="utf-8")

        self.assertIn("PLACA_PARE", payload)
        self.assertIn("PLACA_LOMBADA", payload)
        self.assertFalse(result.best_weights.exists())


if __name__ == "__main__":
    unittest.main()
