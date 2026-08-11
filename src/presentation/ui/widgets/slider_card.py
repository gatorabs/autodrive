from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from src.presentation.ui.theme.tokens import Space
from src.presentation.ui.widgets.card import Card
from src.presentation.ui.widgets.slider_control import SliderControl, SliderSpec


class SliderCard(Card):
    def __init__(
        self,
        title: str,
        specs: list[SliderSpec],
        tk_controls,
        calibration_data,
        on_change: Callable[[str, float], None],
        accent: str = "primary",
        icon_name: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(title, accent=accent, icon_name=icon_name, parent=parent)
        self.controls: dict[str, SliderControl] = {}
        for spec in specs:
            value = calibration_data.get(spec.key, tk_controls.get(spec.key, spec.min_value))
            control = SliderControl(spec, value, on_change, accent=accent)
            self.body_layout.addWidget(control)
            self.controls[spec.key] = control
        self.body_layout.addSpacing(Space.XS)

    def set_value(self, key: str, value: float) -> None:
        if key in self.controls:
            self.controls[key].set(value, notify=False)


class SettingsPanel(Card):
    def __init__(
        self,
        title: str | None,
        *,
        icon_name: str | None = None,
        accent: str = "primary",
        parent: QWidget | None = None,
    ):
        super().__init__(title, accent=accent, icon_name=icon_name, bordered=False, parent=parent)
        self.accent = accent
        self.controls: dict[str, SliderControl] = {}

    def add_section(self, label: str) -> None:
        if self.body_layout.count() > 0:
            self.body_layout.addSpacing(Space.SM)
        section_label = QLabel(label.upper(), self.body)
        section_label.setObjectName("SectionLabel")
        self.body_layout.addWidget(section_label)
        rule = QFrame(self.body)
        rule.setObjectName("SectionRule")
        rule.setFrameShape(QFrame.Shape.HLine)
        self.body_layout.addWidget(rule)
        self.body_layout.addSpacing(2)

    def add_sliders(
        self,
        specs: list[SliderSpec],
        tk_controls,
        calibration_data,
        on_change: Callable[[str, float], None],
    ) -> None:
        for spec in specs:
            value = calibration_data.get(spec.key, tk_controls.get(spec.key, spec.min_value))
            control = SliderControl(spec, value, on_change, accent=self.accent)
            self.body_layout.addWidget(control)
            self.controls[spec.key] = control
        self.body_layout.addSpacing(Space.XS)

    def add_content(self, builder: Callable[[QWidget], None]) -> QWidget:
        frame = QWidget(self.body)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 4)
        self.body_layout.addWidget(frame)
        builder(frame)
        return frame

    def set_value(self, key: str, value: float) -> None:
        if key in self.controls:
            self.controls[key].set(value, notify=False)
