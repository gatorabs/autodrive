import customtkinter as ctk

from src.presentation.ui.components.video_frame import VideoFrame
from .sections.manual_controls_section import ManualControls
from ...components.steering_wheel import SteeringWheel
from src.infrastructure.adapters.video.video_utility_process import get_video_files_from_folder


class ManualModeTab(ctk.CTkFrame):
    def __init__(self, master, tk_controls, calibration_data, shared_controls, init_data, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.shared_controls = shared_controls
        self.init_data = init_data

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure((0, 1, 2, 3, 4), weight=0)

        self.central_video_frame_manual_tab = VideoFrame(
            master=self,
            shared_controls=shared_controls,
            title="Vídeo Central",
        )
        self.central_video_frame_manual_tab.grid(
            row=0, column=0, pady=(10, 5), padx=10, sticky="n"
        )

        self.source_frame_manual_tab = ctk.CTkFrame(self)
        self.source_frame_manual_tab.grid(row=1, column=0, pady=5, padx=10, sticky="n")

        ctk.CTkLabel(self.source_frame_manual_tab, text="Fonte de Vídeo").pack(pady=(5, 0))

        cams = tk_controls.get("DETECTED_CAMERAS", [])
        sources_manual_tab = [f"Câmera {c}" for c in cams] + get_video_files_from_folder()

        default_source = init_data.get("LANE_SOURCE_TAB2", "")
        if str(default_source).isdigit():
            default_source = f"Câmera {default_source}"

        self.lane_source_combo_manual_tab = ctk.CTkComboBox(
            self.source_frame_manual_tab,
            values=sources_manual_tab,
            variable=ctk.StringVar(value=default_source),
            width=master.VIDEO_WIDTH,
        )
        self.lane_source_combo_manual_tab.pack(pady=5)

        button_row = ctk.CTkFrame(self.source_frame_manual_tab, fg_color="transparent")
        button_row.pack(pady=(5, 0))

        ctk.CTkButton(
            button_row,
            text="Aplicar",
            width=120,
            command=master.apply_lane_source_manual_tab,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_row,
            text="Atualizar",
            width=120,
            command=master.refresh_sources_manual_tab,
        ).pack(side="left", padx=5)

        self.manual_controls = ManualControls(
            self,
            tk_controls,
            calibration_data,
            shared_controls,
            on_direction_change=master._on_slider_direction_change,
            fg_color="#2b2b2b",
        )
        self.manual_controls.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="n")

        self.toggles_section = None

        self.steering_wheel = SteeringWheel(
            self,
            command=master._on_wheel_change,
        )
        self.steering_wheel.grid(row=4, column=0, pady=(10, 10))
