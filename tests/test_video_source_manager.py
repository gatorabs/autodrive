from unittest.mock import MagicMock
import sys
import types

# Fake heavy dependencies so the module can be imported without them
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
numpy_module = types.ModuleType("numpy")
numpy_module.ndarray = object
sys.modules.setdefault("numpy", numpy_module)
pil = types.ModuleType("PIL")
pil_image = types.ModuleType("PIL.Image")
pil.Image = pil_image
sys.modules.setdefault("PIL", pil)
sys.modules.setdefault("PIL.Image", pil_image)

from src.infrastructure.adapters.video import video_utility_process as vup
from src.infrastructure.adapters.video.video_utility_process import VideoSourceManager
from src.infrastructure.logging.logger import Logger


def test_open_video_source_warns_once_and_respects_cooldown(monkeypatch, capsys):
    manager = VideoSourceManager("0")
    safe_calls = []

    def safe_stop(q, sc, log, reason):
        safe_calls.append(reason)

    mock_vp = MagicMock(side_effect=RuntimeError("fail"))
    monkeypatch.setattr(vup, "VideoProcessor", mock_vp)

    times = [0.0]
    monkeypatch.setattr(vup.time, "monotonic", lambda: times[0])

    logger = Logger("Test", verbose=True)

    manager.open_video_source(None, {}, logger, safe_stop, cooldown=2.0)
    assert mock_vp.call_count == 1
    assert "Falha ao abrir fonte" in capsys.readouterr().out
    assert len(safe_calls) == 1

    manager.open_video_source(None, {}, logger, safe_stop, cooldown=2.0)
    assert mock_vp.call_count == 1
    assert capsys.readouterr().out == ""
    assert len(safe_calls) == 1

    times[0] = 3.0
    manager.open_video_source(None, {}, logger, safe_stop, cooldown=2.0)
    assert mock_vp.call_count == 2
    assert capsys.readouterr().out == ""
    assert len(safe_calls) == 1


def test_success_resets_warning(monkeypatch, capsys):
    manager = VideoSourceManager("0")
    safe_calls = []

    def safe_stop(q, sc, log, reason):
        safe_calls.append(reason)

    first = MagicMock(side_effect=[RuntimeError("fail"), object()])
    monkeypatch.setattr(vup, "VideoProcessor", first)

    times = [0.0]
    monkeypatch.setattr(vup.time, "monotonic", lambda: times[0])

    logger = Logger("Test", verbose=True)

    assert manager.open_video_source(None, {}, logger, safe_stop) is None
    capsys.readouterr()

    times[0] = 3.0
    assert manager.open_video_source(None, {}, logger, safe_stop) is not None
    assert "Fonte aberta" in capsys.readouterr().out
    assert not manager._warn_unavailable

    second = MagicMock(side_effect=RuntimeError("again"))
    monkeypatch.setattr(vup, "VideoProcessor", second)

    manager.open_video_source(None, {}, logger, safe_stop)
    out = capsys.readouterr().out
    assert "Falha ao abrir fonte" in out
    assert len(safe_calls) == 2
