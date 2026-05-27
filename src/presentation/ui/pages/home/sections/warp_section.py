from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.presentation.ui.components.slider import SliderSection, SliderConfig

class WarpControls(SliderSection):
    """Controls for warp transformation points."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        points = [
            SliderConfig("tl_x", "Topo Esq. X", 0, FRAME_WIDTH),
            SliderConfig("tl_y", "Topo Esq. Y", 0, FRAME_HEIGHT),
            SliderConfig("tr_x", "Topo Dir. X", 0, FRAME_WIDTH),
            SliderConfig("tr_y", "Topo Dir. Y", 0, FRAME_HEIGHT),
            SliderConfig("bl_x", "Base Esq. X", 0, FRAME_WIDTH),
            SliderConfig("bl_y", "Base Esq. Y", 0, FRAME_HEIGHT),
            SliderConfig("br_x", "Base Dir. X", 0, FRAME_WIDTH),
            SliderConfig("br_y", "Base Dir. Y", 0, FRAME_HEIGHT),
        ]
        super().__init__(master, "Perspectiva da Pista", tk_controls, calibration_data, points, **kwargs)
