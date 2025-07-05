from dataclasses import dataclass, field

@dataclass
class LaneDetectionState:
    frame_count: int           = 0
    total_processing_time: float = 0.0
    fps: float                 = 0.0
    avg_time: float            = 0.0
    avg_left: float            = field(default=None)
    avg_right: float           = field(default=None)
    has_ref: bool              = False
    direction: int             = 0
    speed: int                 = 0
