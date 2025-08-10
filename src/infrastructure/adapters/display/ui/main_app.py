import ctypes
import sys

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
from src.infrastructure.adapters.display.ui.pages.home.home_tab import HomeTab
from src.infrastructure.adapters.display.ui.pages.manual_mode.manual_mode_tab import ManualModeTab
from src.infrastructure.adapters.video.begin_the_video import (
    detect_camera_indices,
    get_video_files_from_folder,
)
from .components.tab_manager import TabManager
from src.infrastructure.adapters.display.ui.pages.task_manager.task_manager_tab import TaskManagerTab
from .helpers.main_app_helper import enable_windows_dpi_awareness

enable_windows_dpi_awareness()

logger = Logger("MainUI")

class MainApp(ctk.CTk):
    """Main application window for the UI."""
    def __init__(self, shared_frames, tk_controls, shared_controls, lane_queue):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self._on_close_request)

        self.calibration_data = load_data(CALIBRATION_FILE)
        self.init_data = load_data(DEFAULT_UI_PATH)
        self.title("Autonomous Team")

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

        self._build_home()

        self._build_manual_tab()
        self._build_task_manager_frame()
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
            self.shared_controls["WEBVIEW"] = False
            self.shared_controls["RUNNING"] = False
            refresh_json({"MANUAL_MD": False}, DEFAULT_UI_PATH)
            self.destroy()

    def _build_home(self):
        self.home_frame = HomeTab(
            self,
            self.tk_controls,
            self.calibration_data,
            self.shared_controls,
            self.init_data,
        )

        self.tab_manager.create_tab(
            "Home", self.home_frame, on_right=False, on_select=self.on_home_selected
        )

        self.floating_widget = self.home_frame.floating_widget
        self.normal_frame = self.home_frame.normal_frame
        self.edges_frame = self.home_frame.edges_frame
        self.object_frame = self.home_frame.object_frame
        self.warp_controls = self.home_frame.warp_controls
        self.pid_controls = self.home_frame.pid_controls
        self.filters = self.home_frame.filters
        self.sources_controls = self.home_frame.sources_controls
        self.object_roi_controls = self.home_frame.object_roi_controls
        self.extras_controls = self.home_frame.extras_controls

    def _build_manual_tab(self):
        self.manual_tab = ManualModeTab(
            self,
            self.tk_controls,
            self.calibration_data,
            self.shared_controls,
            self.init_data,
        )

        def on_manual_selected(tab_name):
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
                    self._sync_manual_controls()
            else:
                self.tab_manager.select_tab(tab_name)
                self._sync_manual_controls()

        self.tab_manager.create_tab(
            "Manual Mode", self.manual_tab, on_right=True, on_select=on_manual_selected
        )

        self.central_video_frame_manual_tab = self.manual_tab.central_video_frame_manual_tab
        self.lane_source_combo_manual_tab = self.manual_tab.lane_source_combo_manual_tab
        self.manual_controls = self.manual_tab.manual_controls
        self.toggles_section = self.manual_tab.toggles_section
        self.steering_wheel = self.manual_tab.steering_wheel


    def _build_task_manager_frame(self):
        ctk.set_widget_scaling(1.0)
        self.task_manager_frame = TaskManagerTab(self)
        self.tab_manager.create_tab("Task Manager", self.task_manager_frame, on_right=True)

    def apply_lane_source_manual_tab(self):
        def clean_source(value):
            return value.replace("Câmera ", "") if value.startswith("Câmera ") else value

        selected_source = clean_source(self.lane_source_combo_manual_tab.get())
        self.tk_controls["LANE_SOURCE_TAB2"] = selected_source
        self.shared_controls["LANE_SOURCE_TAB2"] = selected_source

        refresh_json({
            "LANE_SOURCE_TAB2": selected_source
        }, DEFAULT_UI_PATH)

    def refresh_sources_manual_tab(self):
        current = self.lane_source_combo_manual_tab.get()

        exclude = []
        if current.startswith("Câmera "):
            try:
                exclude.append(int(current.replace("Câmera ", "")))
            except ValueError:
                pass

        cameras = detect_camera_indices(exclude_indices=exclude)
        videos = get_video_files_from_folder()
        new_options = [f"Câmera {i}" for i in cameras] + videos

        if current.startswith("Câmera") and current not in new_options:
            new_options.append(current)

        if not new_options:
            return

        self.lane_source_combo_manual_tab.configure(values=new_options)
        if current not in new_options:
            self.lane_source_combo_manual_tab.set(new_options[0])

    def _sync_manual_controls(self):
        last_data = self.shared_controls.get("CAR_INFO", {})

        direction = last_data.get("CAR_DIRECTION_DATA")
        speed = last_data.get("CAR_SPEED_DATA")

        if direction is not None:
            self.manual_controls.set("MANUAL_DIRECTION", direction)
            self.steering_wheel.set_angle(direction, trigger_command=False)
        if speed is not None:
            self.manual_controls.set("MANUAL_SPEED", speed)

    def _on_wheel_change(self, angle: float):
        self.manual_controls.set("MANUAL_DIRECTION", angle)

    def _on_slider_direction_change(self, angle: float):
        self.steering_wheel.set_angle(angle, trigger_command=False)

    def on_tab_change(self, previous, current):
        if previous == "Home" and current != "Home":
            self.floating_widget.close_modal()

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
            shared_manual = self.shared_controls.get("MANUAL_MD", False)
            tk_manual = self.tk_controls.get("MANUAL_MD", False)

            if shared_manual != tk_manual:
                self.tk_controls["MANUAL_MD"] = shared_manual
                refresh_json({"MANUAL_MD": shared_manual}, DEFAULT_UI_PATH)
                if shared_manual:
                    self.tab_manager.select_tab("Manual Mode")
                    self._sync_manual_controls()
                else:
                    self.tab_manager.select_tab("Home")

            if self.tk_controls.get("MANUAL_MD", False):
                car_info = self.shared_controls.get("CAR_INFO", {})
                if car_info != getattr(self.manual_controls, "car_data", {}):
                    self._sync_manual_controls()

            if not self.tk_controls.get("MANUAL_MD", False):
                self.normal_frame.update_image(self.shared_frames.get("NORMAL_FRAME"))
                self.edges_frame.update_image(self.shared_frames.get("EDGES_FRAME"))
                self.object_frame.update_image(self.shared_frames.get("OBJECT_FRAME"))
            else:
                self.central_video_frame_manual_tab.update_image(
                    self.shared_frames.get("TAB2_FRAME")
                )

        except (KeyError, OSError, UnidentifiedImageError) as e:
            logger.error(f"Erro ao atualizar frames: {e}")

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