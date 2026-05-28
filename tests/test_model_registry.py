import json
import tempfile
import unittest
from pathlib import Path

from src.domain.models.detection_model.active_model import ActiveModel
from src.infrastructure.data.repository.model_registry_repository import load_active_model


class ModelRegistryTest(unittest.TestCase):
    def test_returns_none_when_registry_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            active = load_active_model("config/model_registry.json", base_dir=Path(tmp))

        self.assertIsNone(active)

    def test_loads_active_model_with_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model_path = root / "utils" / "model_trainer" / "yolo_runs" / "todos_objetos" / "weights" / "best.pt"
            model_path.parent.mkdir(parents=True)
            model_path.write_bytes(b"fake weight")

            registry_path = root / "config" / "model_registry.json"
            registry_path.parent.mkdir()
            registry_path.write_text(
                json.dumps(
                    {
                        "name": "todos_objetos",
                        "path": "utils/model_trainer/yolo_runs/todos_objetos/weights/best.pt",
                        "classes": ["PLACA_PARE", "PLACA_LOMBADA"],
                        "promoted_at": "2026-05-27T10:00:00",
                        "source": "trainer",
                    }
                ),
                encoding="utf-8",
            )

            active = load_active_model(registry_path, base_dir=root)

        self.assertIsNotNone(active)
        self.assertIsInstance(active, ActiveModel)
        self.assertEqual(active.name, "todos_objetos")
        self.assertEqual(active.classes, ("PLACA_PARE", "PLACA_LOMBADA"))
        self.assertEqual(active.path.name, "best.pt")

    def test_returns_none_when_model_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = root / "config" / "model_registry.json"
            registry_path.parent.mkdir()
            registry_path.write_text(
                json.dumps({"name": "broken", "path": "missing/best.pt"}),
                encoding="utf-8",
            )

            active = load_active_model(registry_path, base_dir=root)

        self.assertIsNone(active)


if __name__ == "__main__":
    unittest.main()
