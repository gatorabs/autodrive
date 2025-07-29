import customtkinter as ctk
from PIL import UnidentifiedImageError
from CTkMessagebox import CTkMessagebox

from src.infrastructure.adapters.calibration.calibration_repository import load_data, refresh_json
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULT_UI_PATH, DEFAULTS_FILE
from src.infrastructure.logging.logger import Logger

from src.infrastructure.constants.ui_constants.component_constants import (
    FRAME_WIDTH_T,
    FRAME_HEIGHT_T,
    WARP_SECTION_HEIGHT,
    PID_SECTION_HEIGHT,
    OBJECT_ROI_SECTION_HEIGHT,
    EXTRAS_SECTION_HEIGHT,
    COMS_SECTION_HEIGHT,
    FILTERS_SECTION_HEIGHT,
    GAP,
    EXTRA_MARGIN,
)
from .components.video_frame import VideoFrame
from .components.filter_controls import FilterControls
from .components.warp_controls import WarpControls
from .components.object_roi_section import ObjectRoiSection
from .components.pid_section import PIDSection
from .components.extras_controls import ExtrasControls
from .components.source_serial_controls import SourceAndSerialControls
from .components.manual_controls import ManualControls
from .components.checkbox_section import CheckboxSection
from src.infrastructure.adapters.video.begin_the_video import (
    detect_camera_indices,
    get_video_files_from_folder,
)
from .components.floating_widget import FloatingWidget
from .components.tab_manager import TabManager

logger = Logger("MainUI")

class MainApp(ctk.CTk):
    """Main application window for the UI."""
    def __init__(self, shared_frames, tk_controls, shared_controls, lane_queue):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self._on_close_request)

        self.calibration_data = load_data(CALIBRATION_FILE)
        self.init_data = load_data(DEFAULT_UI_PATH)
        self.title("Visualizador de Frames com Filtros")

        self.DEFAULTS_FILE = DEFAULTS_FILE
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.shared_controls = shared_controls
        self.lane_queue = lane_queue

        self.VIDEO_WIDTH = FRAME_WIDTH_T
        self.VIDEO_HEIGHT = FRAME_HEIGHT_T

        self.GAP = GAP

        self.video_section_height = self.VIDEO_HEIGHT + 12 + EXTRA_MARGIN
        self.warp_section_height = WARP_SECTION_HEIGHT
        self.pid_section_height = PID_SECTION_HEIGHT

        self.first_column_section_height = self.pid_section_height + self.warp_section_height

        self.object_roi_section_height = OBJECT_ROI_SECTION_HEIGHT
        self.extras_section_height = EXTRAS_SECTION_HEIGHT

        self.last_column_section_height = self.extras_section_height + self.object_roi_section_height

        self.coms_section_height = COMS_SECTION_HEIGHT
        self.filters_section_height = FILTERS_SECTION_HEIGHT
        self.filters_coms_section_height = self.filters_section_height + self.coms_section_height + 5

        lower = max(
            self.first_column_section_height,
            self.filters_coms_section_height,
            self.last_column_section_height,
        ) + EXTRA_MARGIN

        self.TOTAL_HEIGHT = self.video_section_height + lower + 30
        self.TOTAL_WIDTH = self.VIDEO_WIDTH * 3 + self.GAP * 4

        self.geometry(f"{self.TOTAL_WIDTH}x{self.TOTAL_HEIGHT}")
        self.minsize(self.TOTAL_WIDTH, self.TOTAL_HEIGHT)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0,1,2), weight=1)

        self.tab_manager = TabManager(self)
        self.home_frame = ctk.CTkFrame(self)

        self.tab_manager.create_tab("Home", self.home_frame, on_right=False, on_select=self.on_home_selected)
        self._build_home(self.home_frame)

        self._build_tab2_frame()
        self.update_loop()

    def _on_close_request(self):
        box = CTkMessagebox(
            title="Encerrar aplicação",
            message="Deseja realmente encerrar o sistema?",
            icon="question",
            option_1="Sim",
            option_2="Cancelar"
        )

        if box.get() == "Sim":
            self.shared_controls["MANUAL_MD"] = False
            self.shared_controls["RUNNING"] = False
            refresh_json({"MANUAL_MD": False}, DEFAULT_UI_PATH)
            self.destroy()

    def _build_home(self, parent):
        parent.grid_rowconfigure((0, 1), weight=0)
        parent.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

        self.floating_widget = FloatingWidget(self, self.tk_controls)

        VIDEO_WIDTH, VIDEO_HEIGHT = FRAME_WIDTH_T, FRAME_HEIGHT_T

        def _add_video_frame(col, name):
            container = ctk.CTkFrame(parent, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fg_color="transparent")
            container.grid(row=0, column=col, padx=10, pady=(10, 2), sticky="nsew")
            container.grid_propagate(False)
            video = VideoFrame(container, self.shared_controls, name)
            video.pack(expand=True, fill="both")
            return video

        self.normal_frame = _add_video_frame(0, "NORMAL_FRAME")
        self.edges_frame = _add_video_frame(1, "EDGES_FRAME")
        self.object_frame = _add_video_frame(2, "OBJECT_FRAME")

        def _make_section(master, height, ControlClass, *args):
            sec = ctk.CTkFrame(master, height=height, fg_color="transparent")
            sec.pack(fill="x", pady=5, padx=10)
            sec.pack_propagate(False)
            ctrl = ControlClass(sec, *args)
            ctrl.pack(expand=True, fill="both")
            return ctrl

        col0 = ctk.CTkFrame(parent, fg_color="transparent")
        col0.grid(row=1, column=0, sticky="nsew")
        self.warp_controls = _make_section(col0, 300, WarpControls, self.tk_controls, self.calibration_data)
        self.pid_controls = _make_section(col0, 165, PIDSection, self.tk_controls, self.calibration_data)

        col1 = ctk.CTkFrame(parent, fg_color="transparent")
        col1.grid(row=1, column=1, sticky="nsew")
        self.filters = _make_section(col1, 110, FilterControls, self.tk_controls, self.calibration_data)
        self.sources_controls = _make_section(col1, 250,
                                              SourceAndSerialControls,
                                              self.tk_controls,
                                              self.calibration_data,
                                              self.shared_controls,
                                              self.init_data
                                              )

        col2 = ctk.CTkFrame(parent, fg_color="transparent")
        col2.grid(row=1, column=2, sticky="nsew")
        self.object_roi_controls = _make_section(col2, 165, ObjectRoiSection, self.tk_controls, self.calibration_data)
        self.extras_controls = _make_section(col2, 280, ExtrasControls,
                                             self.tk_controls, self.shared_controls, self.shared_controls)

    def _build_tab2_frame(self):
        self.tab2_frame = ctk.CTkFrame(self)

        def on_tab2_selected(tab_name):
            if not self.tk_controls.get("MANUAL_MD", False):
                box = CTkMessagebox(
                    title="Atenção",
                    message="Modo manual será ativo",
                    icon="warning",
                    option_1="OK",
                    option_2="Cancelar",
                )
                response = box.get()
                if response == "OK":
                    self.tk_controls["MANUAL_MD"] = True
                    self.shared_controls["MANUAL_MD"] = True
                    refresh_json({"MANUAL_MD": True}, DEFAULT_UI_PATH)
                    self.tab_manager.select_tab(tab_name)
            else:
                self.tab_manager.select_tab(tab_name)

        self.tab_manager.create_tab("Tab 2", self.tab2_frame, on_right=True, on_select=on_tab2_selected)

        self.tab2_frame.columnconfigure(0, weight=1)
        self.tab2_frame.columnconfigure(1, weight=0)
        self.tab2_frame.rowconfigure((0, 1, 2), weight=0)

        self.central_video_frame_tab2 = VideoFrame(
            master=self.tab2_frame,
            shared_controls=self.shared_controls,
            title="Vídeo Central",
        )
        self.central_video_frame_tab2.grid(
            row=0, column=0, pady=(10, 5), padx=10, sticky="n"
        )


        self.source_frame_tab2 = ctk.CTkFrame(self.tab2_frame)
        self.source_frame_tab2.grid(row=1, column=0, pady=5, padx=10, sticky="n")

        ctk.CTkLabel(self.source_frame_tab2, text="Fonte de Vídeo (Tab 2)").pack(pady=(5, 0))

        sources_tab2 = self.tk_controls.get("DETECTED_CAMERAS", []) + get_video_files_from_folder()

        default_source = self.init_data.get("LANE_SOURCE_TAB2", "")

        self.lane_source_combo_tab2 = ctk.CTkComboBox(
            self.source_frame_tab2,
            values=sources_tab2,
            variable=ctk.StringVar(value=default_source),
            width=self.VIDEO_WIDTH
        )
        self.lane_source_combo_tab2.pack(pady=5)

        button_row = ctk.CTkFrame(self.source_frame_tab2, fg_color="transparent")
        button_row.pack(pady=(5, 0))

        ctk.CTkButton(
            button_row,
            text="Aplicar",
            width=120,
            command=self.apply_lane_source_tab2
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_row,
            text="Atualizar",
            width=120,
            command=self.refresh_sources_tab2
        ).pack(side="left", padx=5)

        self.manual_controls = ManualControls(
            self.tab2_frame,
            self.tk_controls,
            self.calibration_data,
            self.lane_queue,
            fg_color="#2b2b2b",
        )
        self.manual_controls.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="n")

        self.toggles_section = CheckboxSection(
            self.tab2_frame,
            labels=["SEND_LOGS"],
            tk_controls=self.tk_controls,
            shared_controls=self.shared_controls,
            orientation="vertical",
        )
        self.toggles_section.grid(row=2, column=1, padx=10, pady=(5, 10), sticky="n")

    def apply_lane_source_tab2(self):
        def clean_source(value):
            return value.replace("Câmera ", "") if value.startswith("Câmera ") else value

        selected_source = clean_source(self.lane_source_combo_tab2.get())
        self.tk_controls["LANE_SOURCE_TAB2"] = selected_source
        self.shared_controls["LANE_SOURCE_TAB2"] = selected_source

        refresh_json({
            "LANE_SOURCE_TAB2": selected_source
        }, DEFAULT_UI_PATH)

    def refresh_sources_tab2(self):
        cameras = detect_camera_indices()
        videos = get_video_files_from_folder()
        new_options = [f"Câmera {i}" for i in cameras] + videos

        if not new_options:
            return

        self.lane_source_combo_tab2.configure(values=new_options)
        current = self.lane_source_combo_tab2.get()
        if current not in new_options:
            self.lane_source_combo_tab2.set(new_options[0])

    def on_home_selected(self, tab_name):
        if self.tk_controls.get("MANUAL_MD", False):
            box = CTkMessagebox(
                title="Atenção",
                message="O Modo manual será desativado",
                icon="info",
                option_1="OK",
                option_2="Cancelar",
            )
            response = box.get()
            if response == "OK":
                self.tk_controls["MANUAL_MD"] = False
                self.shared_controls["MANUAL_MD"] = False
                refresh_json({"MANUAL_MD": False}, DEFAULT_UI_PATH)
                self.tab_manager.select_tab(tab_name)
        else:
            self.tab_manager.select_tab(tab_name)

    def update_loop(self):
        try:
            if not self.tk_controls.get("MANUAL_MD", False):
                self.normal_frame.update_image(self.shared_frames.get("NORMAL_FRAME"))
                self.edges_frame.update_image(self.shared_frames.get("EDGES_FRAME"))
                self.object_frame.update_image(self.shared_frames.get("OBJECT_FRAME"))

            else:
                self.central_video_frame_tab2.update_image(self.shared_frames.get("TAB2_FRAME"))

        except (KeyError, OSError, UnidentifiedImageError) as e:
            logger.error("Erro ao atualizar frames:", e)

        self.after(33, self.update_loop)

    def restore_defaults(self):
        load_data(self.DEFAULTS_FILE, update_target_if_exists=self.tk_controls)
        sections = [
            self.filters,
            self.warp_controls,
            self.object_roi_controls,
            self.extras_controls,
            self.pid_controls,
        ]

        for name, value in self.tk_controls.items():
            for section in sections:
                if name in section.sliders:
                    section.set(name, value)
        refresh_json(self.tk_controls, CALIBRATION_FILE, only_existing_keys=True)

def launch_homepage(shared_frames, tk_controls, shared_controls, lane_queue):
    app = MainApp(shared_frames, tk_controls, shared_controls, lane_queue)
    app.resizable(False, False)
    app.mainloop()
