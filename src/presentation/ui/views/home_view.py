from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.infrastructure.adapters.serial.serial_communicator import SerialCommunicator
from src.infrastructure.constants.path_constants import DEFAULT_UI_PATH
from src.infrastructure.vision.camera_discovery import detect_camera_indices
from src.infrastructure.vision.video_files import get_video_files_from_folder
from src.presentation.ui.theme.tokens import Color, Size, Space
from src.presentation.ui.widgets.combo_box import ComboBox
from src.presentation.ui.widgets.slider_card import SettingsPanel
from src.presentation.ui.widgets.slider_control import SliderSpec
from src.presentation.ui.widgets.video_tile import VideoTile
from src.presentation.ui.widgets.warp_preview import WarpPointsPreview


class HomeView(QWidget):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.sources: list[str] = []
        self.com_ports: list[str] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter)

        video_row = QWidget(splitter)
        video_layout = QHBoxLayout(video_row)
        video_layout.setContentsMargins(Space.MD, Space.SM, Space.MD, Space.SM)
        video_layout.setSpacing(Size.ROW_GAP)
        self.normal_video = VideoTile("Normal Frame", "Waiting for normal frame", "lane")
        self.edges_video = VideoTile("Edges Frame", "Waiting for edges frame", "lane")
        self.object_video = VideoTile("Object Frame", "Waiting for object frame", "object")
        for tile in (self.normal_video, self.edges_video, self.object_video):
            video_layout.addWidget(tile, 1)
        splitter.addWidget(video_row)

        self.camera_panel = self._build_camera_panel()
        self.detection_panel = self._build_detection_panel()
        self.object_panel = self._build_object_panel()

        tabs = QTabWidget(splitter)
        for title, panel in (
            ("Camera & Perspective", self.camera_panel),
            ("Detection Tuning", self.detection_panel),
            ("Object Detection", self.object_panel),
        ):
            tab_scroll = QScrollArea()
            tab_scroll.setWidgetResizable(True)
            tab_scroll.setWidget(panel)
            tabs.addTab(tab_scroll, title)
        splitter.addWidget(tabs)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 640])

    def _build_camera_panel(self) -> SettingsPanel:
        panel = SettingsPanel("Camera & Perspective", icon_name="camera", accent="primary")
        panel.add_section("Video Sources")
        panel.add_content(self._build_video_sources_content)
        panel.add_section("Serial Ports")
        panel.add_content(self._build_serial_ports_content)
        panel.add_section("Warp Points")
        warp_preview = WarpPointsPreview()
        panel.add_content(lambda frame, w=warp_preview: frame.layout().addWidget(w))
        panel.add_sliders(
            [
                SliderSpec("tl_x", "Top Left X", 0, 640),
                SliderSpec("tl_y", "Top Left Y", 0, 480),
                SliderSpec("tr_x", "Top Right X", 0, 640),
                SliderSpec("tr_y", "Top Right Y", 0, 480),
                SliderSpec("bl_x", "Bottom Left X", 0, 640),
                SliderSpec("bl_y", "Bottom Left Y", 0, 480),
                SliderSpec("br_x", "Bottom Right X", 0, 640),
                SliderSpec("br_y", "Bottom Right Y", 0, 480),
            ],
            self.controller.tk_controls,
            self.controller.calibration_data,
            self.controller.on_slider_value,
        )
        self._wire_warp_preview(panel, warp_preview)
        return panel

    @staticmethod
    def _wire_warp_preview(panel: SettingsPanel, preview: WarpPointsPreview) -> None:
        keys = ("tl_x", "tl_y", "tr_x", "tr_y", "bl_x", "bl_y", "br_x", "br_y")

        def refresh() -> None:
            c = panel.controls
            preview.set_points(
                (c["tl_x"].get(), c["tl_y"].get()),
                (c["tr_x"].get(), c["tr_y"].get()),
                (c["bl_x"].get(), c["bl_y"].get()),
                (c["br_x"].get(), c["br_y"].get()),
            )

        for key in keys:
            control = panel.controls[key]
            original = control.on_change
            control.on_change = lambda k, v, _orig=original: (_orig(k, v), refresh())
        refresh()

    def _build_detection_panel(self) -> SettingsPanel:
        panel = SettingsPanel("Detection Tuning", icon_name="options", accent="secondary")
        panel.add_section("Image Filters")
        panel.add_sliders(
            [SliderSpec("F_Canny", "Canny Low", 0, 255), SliderSpec("S_Canny", "Canny High", 0, 255)],
            self.controller.tk_controls,
            self.controller.calibration_data,
            self.controller.on_slider_value,
        )
        panel.add_section("PID Control")
        panel.add_sliders(
            [
                SliderSpec("KP", "Proportional", 0.0, 5.0, 0.01),
                SliderSpec("KI", "Integral", 0.0, 10.0, 0.001),
                SliderSpec("KD", "Derivative", 0.0, 10.0, 0.001),
            ],
            self.controller.tk_controls,
            self.controller.calibration_data,
            self.controller.on_slider_value,
        )
        panel.add_section("Operation")
        panel.add_sliders(
            [
                SliderSpec("Lines", "Lines", 0, 480),
                SliderSpec("Distance", "Distance", 0, 270),
                SliderSpec("Speed", "Speed", 0, 255),
                SliderSpec("Side", "Side", 1, 2),
            ],
            self.controller.tk_controls,
            self.controller.calibration_data,
            self.controller.on_slider_value,
        )
        return panel

    def _build_object_panel(self) -> SettingsPanel:
        panel = SettingsPanel("Object Detection", icon_name="target", accent="success")
        panel.add_section("Traffic")
        panel.add_sliders(
            [
                SliderSpec("Person", "Person", 0, 240),
                SliderSpec("SEMAFORO", "Traffic Light", 0, 240),
                SliderSpec("PeopleRegion", "Person Region", 10, 100),
            ],
            self.controller.tk_controls,
            self.controller.calibration_data,
            self.controller.on_slider_value,
        )
        panel.add_section("Signs")
        panel.add_sliders(
            [
                SliderSpec("PLACA_PARE", "Stop Sign", 0, 240),
                SliderSpec("PLACA_DESVIO", "Detour Sign", 0, 240),
                SliderSpec("PLACA_LOMBADA", "Speed Bump Sign", 0, 240),
            ],
            self.controller.tk_controls,
            self.controller.calibration_data,
            self.controller.on_slider_value,
        )
        return panel

    def _build_video_sources_content(self, frame: QWidget) -> None:
        self.refresh_source_options()
        init_data = self.controller.init_data
        lane = self._display_source(init_data.get("LANE_SOURCE", ""))
        obj = self._display_source(init_data.get("OBJECT_SOURCE", ""))

        layout = frame.layout()
        self.lane_combo = self._combo_row(layout, "Lane camera", self.sources, lane)
        self.object_combo = self._combo_row(layout, "Object camera", self.sources, obj)

        row = QHBoxLayout()
        apply_sources_btn = QPushButton("Apply sources")
        apply_sources_btn.setProperty("variant", "primary")
        apply_sources_btn.clicked.connect(self.apply_sources)
        refresh_sources_btn = QPushButton("Refresh sources")
        refresh_sources_btn.clicked.connect(self.update_sources)
        row.addWidget(apply_sources_btn)
        row.addWidget(refresh_sources_btn)
        layout.addLayout(row)

    def _build_serial_ports_content(self, frame: QWidget) -> None:
        self.refresh_com_options()

        layout = frame.layout()
        self.security_combo = self._combo_row(
            layout, "Safety COM", self.com_ports, self.controller.shared_controls.security_com or ""
        )
        self.sender_combo = self._combo_row(
            layout, "Sender COM", self.com_ports, self.controller.shared_controls.sender_com or ""
        )

        row = QHBoxLayout()
        apply_coms_btn = QPushButton("Apply COMs")
        apply_coms_btn.setProperty("variant", "primary")
        apply_coms_btn.clicked.connect(self.apply_coms)
        refresh_ports_btn = QPushButton("Refresh ports")
        refresh_ports_btn.clicked.connect(self.update_coms)
        row.addWidget(apply_coms_btn)
        row.addWidget(refresh_ports_btn)
        layout.addLayout(row)

    @staticmethod
    def _combo_row(layout, label: str, values: list[str], current: str) -> ComboBox:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {Color.MUTED};")
        combo = ComboBox()
        combo.setEditable(True)
        combo.addItems(values)
        combo.setCurrentText(str(current))
        row.addWidget(lbl)
        row.addWidget(combo, 1)
        layout.addLayout(row)
        return combo

    def refresh_source_options(self) -> None:
        cameras = self.controller.tk_controls.get("DETECTED_CAMERAS", [])
        self.sources = [f"Camera {c}" for c in cameras] + get_video_files_from_folder()

    def refresh_com_options(self) -> None:
        self.com_ports = SerialCommunicator.list_available_ports()

    def update_sources(self) -> None:
        current_lane = self.lane_combo.currentText()
        current_object = self.object_combo.currentText()
        exclude = []
        for current in (current_lane, current_object):
            if current.startswith("Camera "):
                try:
                    exclude.append(int(current.replace("Camera ", "")))
                except ValueError:
                    pass
        cameras = detect_camera_indices(exclude_indices=exclude)
        videos = get_video_files_from_folder()
        self.sources = [f"Camera {i}" for i in cameras] + videos
        if not self.sources:
            self.controller.show_status("No sources found", "warning")
            return
        self._set_combo_items(self.lane_combo, self.sources)
        self._set_combo_items(self.object_combo, self.sources)

    def update_coms(self) -> None:
        self.refresh_com_options()
        self._set_combo_items(self.security_combo, self.com_ports)
        self._set_combo_items(self.sender_combo, self.com_ports)
        if not self.com_ports:
            self.controller.show_status("No COM ports found", "warning")

    @staticmethod
    def _set_combo_items(combo: ComboBox, values: list[str]) -> None:
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        combo.setCurrentText(current)
        combo.blockSignals(False)

    def apply_sources(self) -> None:
        lane = self._clean_source(self.lane_combo.currentText())
        obj = self._clean_source(self.object_combo.currentText())
        self.controller.tk_controls.lane_source = lane
        self.controller.tk_controls.object_source = obj
        self.controller.settings_store.update({"LANE_SOURCE": lane, "OBJECT_SOURCE": obj}, DEFAULT_UI_PATH)
        self.controller.show_status("Sources applied", "success")

    def apply_coms(self) -> None:
        sender = self.sender_combo.currentText()
        security = self.security_combo.currentText()
        self.controller.shared_controls.send_data = bool(sender) and sender in self.com_ports
        self.controller.shared_controls.sender_com = sender
        self.controller.shared_controls.security_com = security
        self.controller.settings_store.update({"SENDER_COM": sender, "SECURITY_COM": security}, DEFAULT_UI_PATH)
        self.controller.show_status("COM ports applied", "success")

    def sync_dynamic_ranges(self) -> None:
        max_height = self.controller.shared_controls.get("MAX_HEIGHT")
        if isinstance(max_height, (int, float)) and max_height > 0:
            control = self.detection_panel.controls.get("Lines")
            if control and control.spec.max_value != max_height:
                control.spec = SliderSpec("Lines", "Lines", 0, max_height)
                control.set(control.get(), notify=False)

    @staticmethod
    def _clean_source(value: str) -> str:
        return value.replace("Camera ", "") if value.startswith("Camera ") else value

    @staticmethod
    def _display_source(value) -> str:
        return f"Camera {value}" if str(value).isdigit() else value
