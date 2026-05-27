import tempfile
import unittest
from pathlib import Path

from utils.model_trainer.services.capture_service import (
    CaptureTarget,
    bbox_inside_frame,
    bbox_to_yolo,
    slugify,
)


class CaptureServiceTest(unittest.TestCase):
    def test_slugify_keeps_dataset_folder_stable(self):
        self.assertEqual(slugify("Placa Pare", "fallback"), "Placa-Pare")
        self.assertEqual(slugify("   ", "fallback"), "fallback")

    def test_bbox_to_yolo_uses_normalized_coordinates(self):
        xc, yc, width, height = bbox_to_yolo(10, 20, 40, 60, 100, 200)

        self.assertAlmostEqual(xc, 0.3)
        self.assertAlmostEqual(yc, 0.25)
        self.assertAlmostEqual(width, 0.4)
        self.assertAlmostEqual(height, 0.3)

    def test_bbox_inside_frame_rejects_out_of_bounds_boxes(self):
        self.assertTrue(bbox_inside_frame(100, 100, 10, 10, 20, 20))
        self.assertFalse(bbox_inside_frame(100, 100, -1, 10, 20, 20))
        self.assertFalse(bbox_inside_frame(100, 100, 90, 90, 20, 20))

    def test_capture_target_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = CaptureTarget("PLACA_PARE", 0, Path(tmp) / "PLACA_PARE")

            self.assertEqual(target.images_dir.name, "images")
            self.assertEqual(target.labels_dir.name, "labels")


if __name__ == "__main__":
    unittest.main()
