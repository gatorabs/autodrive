import customtkinter as ctk

from src.presentation.ui.components.video_frame import VideoFrame
from .sections.filter_section import FilterControls
from .sections.warp_section import WarpControls
from .sections.object_roi_section import ObjectRoiSection
from .sections.pid_section import PIDSection
from .sections.extras_section import ExtrasControls
from .sections.source_serial_section import SourceAndSerialControls
from src.infrastructure.constants.ui_constants.component_constants import (
    FRAME_WIDTH_T,
    FRAME_HEIGHT_T,
)
from ...components.floating_widget import FloatingWidget, SettingsFloatingWidget

class HomeTab(ctk.CTkFrame):
    def __init__(self, master, tk_controls, calibration_data, shared_controls, init_data, **kwargs):
        super().__init__(master, fg_color="#121212", **kwargs)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.shared_controls = shared_controls
        self.init_data = init_data

        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

        toolbar_parent = getattr(getattr(master, "tab_manager", None), "right", master)
        self.settings_widget = SettingsFloatingWidget(
            toolbar_parent,
            tk_controls,
            calibration_data,
            auto_place=False,
        )
        self.settings_widget.pack(side="left", padx=(0, 8))
        self.floating_widget = FloatingWidget(
            toolbar_parent,
            tk_controls,
            shared_controls,
            auto_place=False,
        )
        self.floating_widget.pack(side="left", padx=(0, 12))

        VIDEO_WIDTH, VIDEO_HEIGHT = FRAME_WIDTH_T, FRAME_HEIGHT_T

        def _add_video_frame(col, name):
            container = ctk.CTkFrame(
                self,
                width=VIDEO_WIDTH + 18,
                height=VIDEO_HEIGHT + 48,
                fg_color="transparent",
            )
            container.grid(row=0, column=col, padx=10, pady=(8, 6), sticky="nsew")
            container.grid_propagate(False)
            video = VideoFrame(container, shared_controls, name)
            video.pack(expand=True, fill="both")
            return video

        self.normal_frame = _add_video_frame(0, "NORMAL_FRAME")
        self.edges_frame = _add_video_frame(1, "EDGES_FRAME")
        self.object_frame = _add_video_frame(2, "OBJECT_FRAME")

        def _make_section(master_section, height, ControlClass, *args):
            sec = ctk.CTkFrame(
                master_section,
                height=height,
                fg_color="#1f1f1f",
                corner_radius=8,
                border_width=1,
                border_color="#303030",
            )
            sec.pack(fill="x", pady=6, padx=10)
            sec.pack_propagate(False)
            ctrl = ControlClass(sec, *args)
            ctrl.pack(expand=True, fill="both")
            return ctrl

        col0 = ctk.CTkFrame(self, fg_color="transparent")
        col0.grid(row=1, column=0, sticky="nsew")
        self.sources_controls = _make_section(
            col0,
            250,
            SourceAndSerialControls,
            tk_controls,
            calibration_data,
            shared_controls,
            init_data,
        )
        self.filters = _make_section(col0, 100, FilterControls, tk_controls, calibration_data)

        col1 = ctk.CTkFrame(self, fg_color="transparent")
        col1.grid(row=1, column=1, sticky="nsew")
        self.warp_controls = _make_section(col1, 265, WarpControls, tk_controls, calibration_data)
        self.pid_controls = _make_section(col1, 120, PIDSection, tk_controls, calibration_data)

        col2 = ctk.CTkFrame(self, fg_color="transparent")
        col2.grid(row=1, column=2, sticky="nsew")
        self.extras_controls = _make_section(col2, 160, ExtrasControls, tk_controls, calibration_data, shared_controls)
        self.object_roi_controls = _make_section(
            col2,
            220,
            ObjectRoiSection,
            tk_controls,
            calibration_data,
        )

