from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget

from src.infrastructure.constants.path_constants import DEFAULT_UI_PATH
from src.infrastructure.vision.camera_discovery import detect_camera_indices
from src.infrastructure.vision.video_files import get_video_files_from_folder
from src.presentation.ui.theme.tokens import Size, Space
from src.presentation.ui.widgets.card import Card
from src.presentation.ui.widgets.slider_card import SliderCard
from src.presentation.ui.widgets.slider_control import SliderSpec
from src.presentation.ui.widgets.steering_wheel import SteeringWheel
from src.presentation.ui.widgets.video_tile import VideoTile


class ManualView(QWidget):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        grid = QGridLayout(content)
        grid.setContentsMargins(Space.MD, Space.SM, Space.MD, Space.LG)
        grid.setHorizontalSpacing(Size.ROW_GAP)
        grid.setVerticalSpacing(Size.ROW_GAP)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.video = VideoTile("Manual Video", "Waiting for manual frame", "lane")
        grid.addWidget(self.video, 0, 0, 1, 2)

        source_card = Card("Manual Source", accent="secondary", icon_name="camera")
        sources = [f"Camera {c}" for c in controller.tk_controls.get("DETECTED_CAMERAS", [])] + get_video_files_from_folder()
        default = self._display_source(controller.init_data.get("LANE_SOURCE_TAB2", ""))
        self.source_combo = QComboBox()
        self.source_combo.setEditable(True)
        self.source_combo.addItems(sources)
        self.source_combo.setCurrentText(default)
        source_card.body_layout.addWidget(self.source_combo)

        row = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.setProperty("variant", "primary")
        apply_btn.clicked.connect(self.apply_source)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_sources)
        row.addWidget(apply_btn)
        row.addWidget(refresh_btn)
        source_card.body_layout.addLayout(row)
        grid.addWidget(source_card, 1, 0, Qt.AlignmentFlag.AlignTop)

        self.control_card = SliderCard(
            "Manual Control",
            [SliderSpec("MANUAL_DIRECTION", "Direction", 0, 180), SliderSpec("MANUAL_SPEED", "Speed", 0, 255)],
            controller.tk_controls,
            controller.calibration_data,
            self._manual_slider_changed,
            accent="secondary",
            icon_name="manual",
        )
        grid.addWidget(self.control_card, 1, 1, Qt.AlignmentFlag.AlignTop)

        self.wheel_card = Card("Steering Wheel", accent="secondary", icon_name="manual")
        self.wheel = SteeringWheel(controller.tk_controls.get("MANUAL_DIRECTION", 90))
        self.wheel.angleChanged.connect(self._wheel_drag)
        self.wheel_card.body_layout.addWidget(self.wheel, 0, Qt.AlignmentFlag.AlignHCenter)
        grid.addWidget(self.wheel_card, 2, 0, 1, 2, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    def apply_source(self) -> None:
        selected = self._clean_source(self.source_combo.currentText())
        self.controller.tk_controls.lane_source_tab2 = selected
        self.controller.shared_controls["LANE_SOURCE_TAB2"] = selected
        self.controller.settings_store.update({"LANE_SOURCE_TAB2": selected}, DEFAULT_UI_PATH)
        self.controller.show_status("Manual source applied", "success")

    def refresh_sources(self) -> None:
        current = self.source_combo.currentText()
        exclude = []
        if current.startswith("Camera "):
            try:
                exclude.append(int(current.replace("Camera ", "")))
            except ValueError:
                pass
        sources = [f"Camera {i}" for i in detect_camera_indices(exclude_indices=exclude)] + get_video_files_from_folder()
        if not sources:
            self.controller.show_status("No manual sources found", "warning")
            return
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItems(sources)
        self.source_combo.setCurrentText(current)
        self.source_combo.blockSignals(False)

    def sync_car_info(self) -> None:
        data = self.controller.shared_controls.car_info
        direction = data.get("CAR_DIRECTION_DATA")
        speed = data.get("CAR_SPEED_DATA")
        if direction is not None:
            self.control_card.set_value("MANUAL_DIRECTION", direction)
            self.wheel.set_angle(direction)
        if speed is not None:
            self.control_card.set_value("MANUAL_SPEED", speed)

    def _manual_slider_changed(self, key: str, value: float) -> None:
        self.controller.tk_controls[key] = value
        lane_data = {
            "CAR_SPEED_DATA": self.controller.tk_controls.get("MANUAL_SPEED", 0),
            "CAR_DIRECTION_DATA": self.controller.tk_controls.get("MANUAL_DIRECTION", 0),
        }
        self.controller.shared_controls.car_info = lane_data
        if key == "MANUAL_DIRECTION":
            self.wheel.set_angle(value)

    def _wheel_drag(self, angle: int) -> None:
        self.control_card.controls["MANUAL_DIRECTION"].set(angle)

    @staticmethod
    def _clean_source(value: str) -> str:
        return value.replace("Camera ", "") if value.startswith("Camera ") else value

    @staticmethod
    def _display_source(value) -> str:
        return f"Camera {value}" if str(value).isdigit() else value
