from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.presentation.ui.components.slider import SliderSection, SliderConfig

class WarpControls(SliderSection):
    """Controls for warp transformation points."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        points = [
            SliderConfig("tl_x", "tl_x", 0, FRAME_WIDTH),
            SliderConfig("tl_y", "tl_y", 0, FRAME_HEIGHT),
            SliderConfig("tr_x", "tr_x", 0, FRAME_WIDTH),
            SliderConfig("tr_y", "tr_y", 0, FRAME_HEIGHT),
            SliderConfig("bl_x", "bl_x", 0, FRAME_WIDTH),
            SliderConfig("bl_y", "bl_y", 0, FRAME_HEIGHT),
            SliderConfig("br_x", "br_x", 0, FRAME_WIDTH),
            SliderConfig("br_y", "br_y", 0, FRAME_HEIGHT),
        ]
        super().__init__(master, "Warp Controls", tk_controls, calibration_data, points, **kwargs)
