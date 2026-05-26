import unittest

from src.application.state import RuntimeControls, SharedFrames, UiControls


class SharedStateTests(unittest.TestCase):
    def test_runtime_controls_flags_and_car_info(self):
        controls = RuntimeControls({"RUNNING": True})

        self.assertTrue(controls.is_running())
        controls.manual_mode = True
        controls.webview = True
        controls.safe_stop = True
        controls.car_info = {"CAR_SPEED_DATA": 42}
        controls.request_shutdown()

        self.assertFalse(controls.is_running())
        self.assertTrue(controls.manual_mode)
        self.assertTrue(controls.webview)
        self.assertTrue(controls.safe_stop)
        self.assertEqual(controls.car_info["CAR_SPEED_DATA"], 42)

    def test_ui_controls_sources(self):
        controls = UiControls({})

        controls.lane_source = "0"
        controls.lane_source_tab2 = "resources/test_videos/test.mp4"
        controls.object_source = "1"
        controls.speed = 120
        controls.side = 2

        self.assertEqual(controls.lane_source, "0")
        self.assertEqual(controls.lane_source_tab2, "resources/test_videos/test.mp4")
        self.assertEqual(controls.object_source, "1")
        self.assertEqual(controls.speed, 120)
        self.assertEqual(controls.side, 2)

    def test_shared_frames_publish_lane_frames(self):
        frames = SharedFrames({})

        frames.camera_frame = b"camera"
        frames.publish_lane_frames(b"normal", b"edges")
        frames.object_frame = b"object"
        frames.tab2_frame = b"manual"

        self.assertEqual(frames.camera_frame, b"camera")
        self.assertEqual(frames.normal_frame, b"normal")
        self.assertEqual(frames.edges_frame, b"edges")
        self.assertEqual(frames.object_frame, b"object")
        self.assertEqual(frames.tab2_frame, b"manual")


if __name__ == "__main__":
    unittest.main()
