import unittest

from src.infrastructure.hardware.cuda_status import detect_cuda_status


class _FakeCuda:
    def __init__(self, available):
        self.available = available

    def is_available(self):
        return self.available

    def get_device_name(self, _index):
        return "NVIDIA Test GPU"


class _FakeTorch:
    def __init__(self, available):
        self.cuda = _FakeCuda(available)


class _BrokenCuda:
    def is_available(self):
        raise RuntimeError("driver unavailable")


class _BrokenTorch:
    cuda = _BrokenCuda()


class CudaUtilsTests(unittest.TestCase):
    def test_reports_cuda_device_when_available(self):
        status = detect_cuda_status(_FakeTorch(True))

        self.assertTrue(status.available)
        self.assertEqual(status.device_name, "NVIDIA Test GPU")
        self.assertIn("CUDA detected", status.message)

    def test_warns_when_cuda_is_unavailable(self):
        status = detect_cuda_status(_FakeTorch(False))

        self.assertFalse(status.available)
        self.assertEqual(status.device_name, "CPU only")
        self.assertIn("CUDA was not detected", status.message)

    def test_cuda_probe_failure_does_not_break_startup(self):
        status = detect_cuda_status(_BrokenTorch())

        self.assertFalse(status.available)
        self.assertIn("CUDA check failed", status.message)


if __name__ == "__main__":
    unittest.main()
