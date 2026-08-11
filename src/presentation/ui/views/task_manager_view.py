from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.infrastructure.hardware.process_monitor import get_active_python_processes
from src.infrastructure.logging.logger import Logger
from src.presentation.ui.charts.bar_chart import BarChartWidget
from src.presentation.ui.runtime_constants import TASK_MANAGER_POLL_INTERVAL_MS
from src.presentation.ui.theme.tokens import Color, Space
from src.presentation.ui.widgets.card import Card
from src.presentation.ui.widgets.combo_box import ComboBox

logger = Logger("TaskManagerUI")


class TaskManagerView(QWidget):
    _data_ready = Signal(dict)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.active = False
        self.has_data = False
        self._fetching = False
        self._chart_labels: list[str] = []
        self._chart_memory: list[float] = []
        self._chart_cpu: list[float] = []
        self._chart_io: list[float] = []

        self._poll_timer = QTimer(self)
        self._poll_timer.setSingleShot(True)
        self._poll_timer.timeout.connect(self._start_refresh)
        self._data_ready.connect(self._on_data)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Space.LG - 2, Space.MD + 2, Space.LG - 2, Space.MD)
        card = Card("Task Manager")
        outer.addWidget(card)

        header = QHBoxLayout()
        self.summary = QLabel("Waiting for data...")
        self.summary.setStyleSheet(f"color: {Color.MUTED}; font-size: {10}px;")
        header.addWidget(self.summary, 1)
        self.compact_check = QCheckBox("Compact")
        self.compact_check.toggled.connect(self._toggle_compact)
        header.addWidget(self.compact_check)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ProcessName", "Id", "Priority", "Memory (MB)"])
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        chart_header = QHBoxLayout()
        self.metric_combo = ComboBox()
        self.metric_combo.addItems(["Memory", "CPU", "IO"])
        self.metric_combo.currentTextChanged.connect(lambda _text: self._draw_chart())
        chart_header.addWidget(self.metric_combo)
        chart_header.addStretch(1)

        self.chart = BarChartWidget()
        self.chart.setMinimumHeight(180)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(Space.SM)
        content_layout.addLayout(header)
        content_layout.addWidget(self.table, 1)
        content_layout.addLayout(chart_header)
        content_layout.addWidget(self.chart)

        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)
        self.loading_progress.setFixedWidth(220)
        loading_layout.addWidget(self.loading_progress, 0, Qt.AlignmentFlag.AlignHCenter)
        loading_label = QLabel("Loading process data...")
        loading_label.setStyleSheet(f"color: {Color.MUTED};")
        loading_layout.addWidget(loading_label, 0, Qt.AlignmentFlag.AlignHCenter)

        self.stack = QStackedWidget()
        self.stack.addWidget(content_widget)
        self.stack.addWidget(loading_widget)
        card.body_layout.addWidget(self.stack, 1)

    def set_active(self, active: bool) -> None:
        self.active = active
        if active:
            if not self.has_data:
                self._show_loading()
            if not self._fetching and not self._poll_timer.isActive():
                self._start_refresh()
        else:
            self._poll_timer.stop()

    def _start_refresh(self) -> None:
        if not self.active or self._fetching:
            return
        self._fetching = True
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self) -> None:
        try:
            data = get_active_python_processes()
        except Exception as exc:  # noqa: BLE001 - background thread must not crash silently.
            logger.error(f"Failed to read process list: {exc}")
            data = {"processes": [], "process_count": 0, "total_ram_mb": 0.0, "system_cpu": 0.0}
        self._data_ready.emit(data)

    def _on_data(self, data: dict) -> None:
        self._fetching = False
        self._hide_loading()
        self.has_data = True
        if self.active:
            self._render_data(data)
            self._poll_timer.start(TASK_MANAGER_POLL_INTERVAL_MS)

    def _render_data(self, data: dict) -> None:
        processes = data.get("processes", [])
        labels, memory, cpu, io_values = [], [], [], []
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(processes))
        for row, proc in enumerate(processes):
            pid = proc.get("pid")
            mem = proc.get("memory_mb", 0.0)
            labels.append(str(pid))
            memory.append(mem)
            cpu.append(proc.get("cpu_percent", 0.0))
            io_values.append(proc.get("io_mb", 0.0))

            self.table.setItem(row, 0, QTableWidgetItem(str(proc.get("name"))))
            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.ItemDataRole.DisplayRole, pid)
            self.table.setItem(row, 1, pid_item)
            self.table.setItem(row, 2, QTableWidgetItem(str(proc.get("priority"))))
            mem_item = QTableWidgetItem()
            mem_item.setData(Qt.ItemDataRole.DisplayRole, round(mem, 2))
            self.table.setItem(row, 3, mem_item)
        self.table.setSortingEnabled(True)

        self.summary.setText(
            f"Python processes: {data.get('process_count', len(processes))} | "
            f"Total RAM: {data.get('total_ram_mb', 0.0):.2f} MB | "
            f"System CPU: {data.get('system_cpu', 0.0):.1f}%"
        )
        self._chart_labels, self._chart_memory, self._chart_cpu, self._chart_io = labels, memory, cpu, io_values
        self._draw_chart()

    def _draw_chart(self) -> None:
        metric = self.metric_combo.currentText()
        if metric == "Memory":
            values, unit = self._chart_memory, "MB"
        elif metric == "CPU":
            values, unit = self._chart_cpu, "% CPU"
        else:
            values, unit = self._chart_io, "I/O MB"
        self.chart.set_data(self._chart_labels, values, unit)

    def _show_loading(self) -> None:
        self.loading_progress.setRange(0, 0)
        self.stack.setCurrentIndex(1)

    def _hide_loading(self) -> None:
        self.stack.setCurrentIndex(0)

    def _toggle_compact(self, checked: bool) -> None:
        self.metric_combo.setVisible(not checked)
        self.chart.setVisible(not checked)
