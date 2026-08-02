from __future__ import annotations

import io
import threading
from dataclasses import dataclass
from typing import Callable

import cv2
import customtkinter as ctk
import numpy as np
from customtkinter import CTkImage
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, UnidentifiedImageError
from tkinter import ttk

from src.bootstrap import (
    build_process_manager,
    create_initializer,
    create_runtime_state,
    terminate_runtime_processes,
)
from src.infrastructure.adapters.serial.serial_communicator import SerialCommunicator
from src.infrastructure.constants.path_constants import (
    CALIBRATION_FILE,
    DEFAULTS_FILE,
    DEFAULT_UI_PATH,
)
from src.infrastructure.data.repository.calibration_repository import default_settings_store
from src.infrastructure.hardware.process_monitor import get_active_python_processes
from src.infrastructure.logging.logger import Logger
from src.infrastructure.vision.camera_discovery import detect_camera_indices
from src.infrastructure.vision.video_files import get_video_files_from_folder
from src.presentation.ui.theme import (
    Theme,
    accent_card_style,
    badge_style,
    button_style,
    card_style,
    font_body,
    font_caption,
    font_display,
    font_heading,
    font_label,
    icon,
    icon_button_style,
    input_style,
    nav_button_style,
)

logger = Logger("MainUI")


@dataclass(frozen=True)
class SliderSpec:
    key: str
    label: str
    min_value: float
    max_value: float
    step: float = 1.0


class Card(ctk.CTkFrame):
    def __init__(self, master, title: str | None = None, *, accent: str | None = None, **kwargs):
        style = accent_card_style(accent) if accent else card_style()
        super().__init__(master, **style, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.header: ctk.CTkFrame | None = None
        self.title_label: ctk.CTkLabel | None = None
        if title:
            self.header = ctk.CTkFrame(self, fg_color="transparent")
            self.header.grid(row=0, column=0, sticky="ew", padx=14, pady=(11, 6))
            self.header.grid_columnconfigure(0, weight=1)
            self.title_label = ctk.CTkLabel(
                self.header,
                text=title,
                font=font_heading(),
                text_color=Theme.TEXT,
            )
            self.title_label.grid(row=0, column=0, sticky="w")

    def set_accessory(self, widget: ctk.CTkBaseClass) -> None:
        if self.header is None:
            return
        widget.grid(row=0, column=1, sticky="e", padx=(8, 0))


class StateBlock(ctk.CTkFrame):
    def __init__(self, master, title: str, message: str, tone: str = "info"):
        super().__init__(
            master,
            fg_color=Theme.PANEL_ALT,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=Theme.RADIUS_SM,
        )
        color = {
            "info": Theme.TEXT,
            "success": Theme.SUCCESS,
            "warning": Theme.WARNING,
            "error": Theme.DANGER,
        }.get(tone, Theme.TEXT)
        ctk.CTkLabel(self, text=title, font=font_heading(), text_color=color).pack(
            anchor="w", padx=14, pady=(12, 2)
        )
        ctk.CTkLabel(
            self,
            text=message,
            text_color=Theme.MUTED,
            justify="left",
            wraplength=520,
        ).pack(anchor="w", padx=14, pady=(0, 12))


class StatusBadge(ctk.CTkLabel):
    def __init__(self, master, text: str, tone: str = "muted"):
        style = badge_style(tone)
        super().__init__(
            master,
            text=f"  {text}  ",
            font=font_caption(),
            corner_radius=Theme.RADIUS_SM,
            height=24,
            **style,
        )

    def set(self, text: str, tone: str = "muted") -> None:
        self.configure(text=f"  {text}  ", **badge_style(tone))


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str, tone: str = "warning"):
        super().__init__(master)
        self.withdraw()
        self.title(title)
        self.configure(fg_color=Theme.BG)
        self.resizable(False, False)
        self.transient(master)
        self.result = False

        wrapper = Card(self)
        wrapper.grid(row=0, column=0, padx=1, pady=1)
        wrapper.grid_columnconfigure(0, weight=1)

        tone_style = badge_style(tone)
        icon_wrap = ctk.CTkFrame(wrapper, width=48, height=48, corner_radius=24, fg_color=tone_style["fg_color"])
        icon_wrap.grid(row=0, column=0, pady=(24, 12))
        icon_wrap.grid_propagate(False)
        ctk.CTkLabel(icon_wrap, image=icon("alert", 20, tone_style["text_color"]), text="").place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(wrapper, text=title, font=font_heading(), text_color=Theme.TEXT).grid(row=1, column=0, padx=28)
        ctk.CTkLabel(
            wrapper, text=message, text_color=Theme.MUTED, wraplength=260, justify="center"
        ).grid(row=2, column=0, padx=28, pady=(6, 24))

        buttons = ctk.CTkFrame(wrapper, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 24))
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(buttons, text="Cancel", **button_style(False), command=self._cancel).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ctk.CTkButton(buttons, text="Confirm", **button_style(True), command=self._confirm).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        self._center_on(master)
        self.deiconify()
        self.grab_set()
        self.focus_force()

    def _center_on(self, master) -> None:
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = master.winfo_rootx() + (master.winfo_width() - width) // 2
        y = master.winfo_rooty() + (master.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _confirm(self) -> None:
        self.result = True
        self.destroy()

    def _cancel(self) -> None:
        self.result = False
        self.destroy()

    @classmethod
    def ask(cls, master, title: str, message: str, tone: str = "warning") -> bool:
        dialog = cls(master, title, message, tone)
        master.wait_window(dialog)
        return dialog.result


class BootView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        shell = Card(self)
        shell.grid(row=0, column=0, sticky="nsew", padx=36, pady=36)
        shell.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkFrame(shell, width=64, height=64, corner_radius=32, fg_color=Theme.PRIMARY_SOFT)
        badge.grid(row=0, column=0, pady=(48, 16))
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, image=icon("manual", 34, Theme.PRIMARY), text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            shell,
            text="Autonomous Team",
            font=font_display(),
            text_color=Theme.TEXT,
        ).grid(row=1, column=0, pady=(0, 4))
        ctk.CTkLabel(
            shell,
            text="Starting dashboard, processes, and devices",
            text_color=Theme.MUTED,
        ).grid(row=2, column=0, pady=(0, 26))

        self.progress = ctk.CTkProgressBar(
            shell,
            height=8,
            corner_radius=4,
            progress_color=Theme.PRIMARY,
            fg_color=Theme.PANEL_SOFT,
        )
        self.progress.grid(row=3, column=0, sticky="ew", padx=54)
        self.progress.set(0)

        self.step_label = ctk.CTkLabel(shell, text="Preparing...", text_color=Theme.MUTED)
        self.step_label.grid(row=4, column=0, pady=(12, 28))

        self.state_slot = ctk.CTkFrame(shell, fg_color="transparent")
        self.state_slot.grid(row=5, column=0, sticky="ew", padx=54, pady=(0, 42))

    def set_progress(self, value: float, message: str) -> None:
        self.progress.set(max(0.0, min(value / 100.0, 1.0)))
        self.step_label.configure(text=message)

    def show_error(self, message: str) -> None:
        for child in self.state_slot.winfo_children():
            child.destroy()
        StateBlock(self.state_slot, "Startup failed", message, "error").pack(fill="x")

    def show_cuda_status(self, available: bool, device_name: str, message: str) -> None:
        for child in self.state_slot.winfo_children():
            child.destroy()
        title = f"CUDA ready: {device_name}" if available else "CUDA recommended"
        tone = "success" if available else "warning"
        StateBlock(self.state_slot, title, message, tone).pack(fill="x")


class VideoTile(Card):
    def __init__(self, master, title: str, placeholder: str, error_key: str):
        super().__init__(master, title)
        self.placeholder = placeholder
        self.error_key = error_key
        self.current_image: Image.Image | None = None
        self.current_frame_ref = None
        self.render_size: tuple[int, int] | None = None
        self.ctk_image = None
        self.resize_job = None

        self.status_dot = ctk.CTkFrame(
            self.header, width=10, height=10, corner_radius=5, fg_color=Theme.SUBTLE
        )
        self.set_accessory(self.status_dot)

        self.image_label = ctk.CTkLabel(
            self,
            text=placeholder,
            text_color=Theme.MUTED,
            fg_color=Theme.PANEL_ALT,
            corner_radius=Theme.RADIUS_SM,
        )
        self.image_label.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.image_label.grid_propagate(False)
        self.image_label.configure(height=Theme.VIDEO_MIN_HEIGHT)
        self.image_label.bind("<Configure>", self._schedule_resize)
        self.grid_rowconfigure(1, weight=1)

    def update_state(self, frame, *, webview=False, safe_stop=False, object_safe_stop=False):
        if webview:
            self._show_text("Webview active")
            self._set_dot(Theme.WARNING)
            return
        if self.error_key == "lane" and safe_stop:
            self._show_text("Transmission error")
            self._set_dot(Theme.DANGER)
            return
        if self.error_key == "object" and object_safe_stop:
            self._show_text("Transmission error")
            self._set_dot(Theme.DANGER)
            return
        if frame is None:
            self._show_text(self.placeholder)
            self._set_dot(Theme.SUBTLE)
            return
        if frame is self.current_frame_ref and self.render_size == self._target_size():
            self._set_dot(Theme.SUCCESS)
            return
        image = self._to_image(frame)
        if image is None:
            self._show_text(self.placeholder)
            self._set_dot(Theme.DANGER)
            return
        self.current_frame_ref = frame
        self.current_image = image
        self._render()
        self._set_dot(Theme.SUCCESS)

    def _set_dot(self, color: str) -> None:
        self.status_dot.configure(fg_color=color)

    def _to_image(self, frame):
        try:
            if isinstance(frame, (bytes, bytearray)):
                return Image.open(io.BytesIO(frame))
            if isinstance(frame, np.ndarray):
                return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except (OSError, UnidentifiedImageError, cv2.error):
            return None
        return None

    def _target_size(self) -> tuple[int, int]:
        width = max(240, self.image_label.winfo_width() - 2)
        height = max(Theme.VIDEO_MIN_HEIGHT, self.image_label.winfo_height() - 2)
        target_height = int(width * 9 / 16)
        if target_height > height:
            target_height = height
            width = int(height * 16 / 9)
        return max(1, width), max(1, target_height)

    def _render(self):
        if self.current_image is None:
            return
        size = self._target_size()
        self.render_size = size
        # BILINEAR trades a little sharpness for much cheaper per-frame cost than
        # LANCZOS, which matters here because this runs on the Tk main thread ~30x/s.
        resized = self.current_image.resize(size, Image.Resampling.BILINEAR)
        self.ctk_image = CTkImage(light_image=resized, dark_image=resized, size=size)
        self.image_label.configure(image=self.ctk_image, text="")

    def _show_text(self, text: str) -> None:
        self.current_image = None
        self.current_frame_ref = None
        self.render_size = None
        self.image_label.configure(image=None, text=text)

    def _schedule_resize(self, _event=None) -> None:
        if self.resize_job is not None:
            self.after_cancel(self.resize_job)
        self.resize_job = self.after(80, self._on_resize)

    def _on_resize(self) -> None:
        self.resize_job = None
        if self.current_image is not None and self.render_size != self._target_size():
            self._render()

    def destroy(self) -> None:
        if self.resize_job is not None:
            try:
                self.after_cancel(self.resize_job)
            except Exception:
                pass
        super().destroy()


_ACCENT_TRACKS = {
    Theme.PRIMARY: (Theme.PRIMARY, "#60a5fa", "#93c5fd"),
    Theme.SECONDARY: (Theme.SECONDARY, "#67e8f9", "#a5f3fc"),
}


class SliderControl(ctk.CTkFrame):
    def __init__(
        self,
        master,
        spec: SliderSpec,
        value: float,
        on_change: Callable[[str, float], None],
        accent: str = Theme.PRIMARY,
    ):
        super().__init__(master, fg_color="transparent")
        self.spec = spec
        self.on_change = on_change
        self.grid_columnconfigure(0, weight=0, minsize=116)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=64)

        ctk.CTkLabel(self, text=spec.label, text_color=Theme.MUTED, font=font_body(), anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=2
        )
        steps = max(1, int(round((spec.max_value - spec.min_value) / spec.step)))
        track_color, button_color, button_hover = _ACCENT_TRACKS.get(accent, _ACCENT_TRACKS[Theme.PRIMARY])
        self.slider = ctk.CTkSlider(
            self,
            from_=spec.min_value,
            to=spec.max_value,
            number_of_steps=steps,
            progress_color=track_color,
            button_color=button_color,
            button_hover_color=button_hover,
            command=self._slider_changed,
        )
        self.slider.grid(row=0, column=1, sticky="ew", pady=2)
        self.entry = ctk.CTkEntry(
            self,
            justify="center",
            fg_color=Theme.INPUT,
            border_color=Theme.BORDER_HOVER,
            corner_radius=Theme.RADIUS_SM,
            text_color=track_color,
            font=font_label(),
            width=64,
        )
        self.entry.grid(row=0, column=2, padx=(8, 0), pady=2)
        self.entry.bind("<Return>", self._entry_changed)
        self.entry.bind("<FocusOut>", self._entry_changed)
        self.set(value, notify=False)

    def set(self, value: float, *, notify=True) -> None:
        value = self._normalize(value)
        self.slider.set(value)
        self.entry.delete(0, "end")
        self.entry.insert(0, self._format(value))
        if notify:
            self.on_change(self.spec.key, value)

    def _slider_changed(self, value) -> None:
        self.set(value)

    def _entry_changed(self, _event=None) -> None:
        try:
            value = float(self.entry.get())
        except ValueError:
            value = self.slider.get()
        self.set(value)

    def _normalize(self, value: float):
        value = max(self.spec.min_value, min(float(value), self.spec.max_value))
        stepped = round((value - self.spec.min_value) / self.spec.step) * self.spec.step + self.spec.min_value
        return int(round(stepped)) if self.spec.step >= 1 else stepped

    def _format(self, value) -> str:
        return f"{value:.3f}" if self.spec.step < 1 else str(int(round(value)))


class SliderCard(Card):
    def __init__(
        self,
        master,
        title: str,
        specs: list[SliderSpec],
        tk_controls,
        calibration_data,
        on_change: Callable[[str, float], None],
        accent: str = Theme.PRIMARY,
    ):
        super().__init__(master, title, accent=accent)
        self.controls: dict[str, SliderControl] = {}
        for row, spec in enumerate(specs, start=1):
            value = calibration_data.get(spec.key, tk_controls.get(spec.key, spec.min_value))
            control = SliderControl(self, spec, value, on_change, accent=accent)
            control.grid(row=row, column=0, sticky="ew", padx=14, pady=0)
            self.controls[spec.key] = control

    def set_value(self, key: str, value: float) -> None:
        if key in self.controls:
            self.controls[key].set(value, notify=False)


class HomeView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=Theme.BG)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=6)
        self.scroll.grid_columnconfigure((0, 1, 2), weight=1, uniform="home")
        self.scroll.grid_rowconfigure(0, weight=1, uniform="video-row")

        self.normal_video = VideoTile(self.scroll, "Normal Frame", "Waiting for normal frame", "lane")
        self.edges_video = VideoTile(self.scroll, "Edges Frame", "Waiting for edges frame", "lane")
        self.object_video = VideoTile(self.scroll, "Object Frame", "Waiting for object frame", "object")
        for col, tile in enumerate((self.normal_video, self.edges_video, self.object_video)):
            tile.grid(row=0, column=col, sticky="nsew", padx=Theme.ROW_GAP // 2, pady=Theme.ROW_GAP // 2)

        self.warp_card = self._slider_card(
            "Road Perspective",
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
            1,
            0,
            rowspan=3,
        )

        self._build_sources(row=1, column=1)
        self.filter_card = self._slider_card(
            "Image Filters",
            [SliderSpec("F_Canny", "Canny Low", 0, 255), SliderSpec("S_Canny", "Canny High", 0, 255)],
            2,
            1,
        )
        self.pid_card = self._slider_card(
            "PID Control",
            [
                SliderSpec("KP", "Proportional", 0.0, 5.0, 0.01),
                SliderSpec("KI", "Integral", 0.0, 10.0, 0.001),
                SliderSpec("KD", "Derivative", 0.0, 10.0, 0.001),
            ],
            3,
            1,
        )
        self.extras_card = self._slider_card(
            "Operation",
            [
                SliderSpec("Lines", "Lines", 0, 480),
                SliderSpec("Distance", "Distance", 0, 270),
                SliderSpec("Speed", "Speed", 0, 255),
                SliderSpec("Side", "Side", 1, 2),
            ],
            1,
            2,
        )
        self.object_card = self._slider_card(
            "Object Detection",
            [
                SliderSpec("Person", "Person", 0, 240),
                SliderSpec("SEMAFORO", "Traffic Light", 0, 240),
                SliderSpec("PeopleRegion", "Person Region", 10, 100),
                SliderSpec("PLACA_PARE", "Stop Sign", 0, 240),
                SliderSpec("PLACA_DESVIO", "Detour Sign", 0, 240),
                SliderSpec("PLACA_LOMBADA", "Speed Bump Sign", 0, 240),
            ],
            2,
            2,
            rowspan=2,
        )

    def _build_sources(self, row, column):
        card = Card(self.scroll, "Input and Communication")
        card.grid(row=row, column=column, sticky="nsew", padx=Theme.ROW_GAP // 2, pady=Theme.ROW_GAP // 2)

        self.refresh_source_options()
        self.refresh_com_options()
        init_data = self.app.init_data
        lane = self._display_source(init_data.get("LANE_SOURCE", ""))
        obj = self._display_source(init_data.get("OBJECT_SOURCE", ""))

        self.lane_source = ctk.StringVar(value=lane)
        self.object_source = ctk.StringVar(value=obj)
        self.security_com = ctk.StringVar(value=self.app.shared_controls.security_com)
        self.sender_com = ctk.StringVar(value=self.app.shared_controls.sender_com)

        self.lane_combo = self._combo_row(card, 1, "Lane camera", self.sources, self.lane_source)
        self.object_combo = self._combo_row(card, 2, "Object camera", self.sources, self.object_source)
        self.security_combo = self._combo_row(card, 3, "Safety COM", self.com_ports, self.security_com)
        self.sender_combo = self._combo_row(card, 4, "Sender COM", self.com_ports, self.sender_com)

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=5, column=0, sticky="ew", padx=14, pady=(8, 10))
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(buttons, text="Apply sources", **button_style(True), command=self.apply_sources).grid(
            row=0, column=0, sticky="ew", padx=(0, 4), pady=3
        )
        ctk.CTkButton(buttons, text="Refresh sources", **button_style(), command=self.update_sources).grid(
            row=0, column=1, sticky="ew", padx=(4, 0), pady=3
        )
        ctk.CTkButton(buttons, text="Apply COMs", **button_style(True), command=self.apply_coms).grid(
            row=1, column=0, sticky="ew", padx=(0, 4), pady=3
        )
        ctk.CTkButton(buttons, text="Refresh ports", **button_style(), command=self.update_coms).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=3
        )

    def _combo_row(self, parent, row, label, values, variable):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="ew", padx=14, pady=2)
        wrapper.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(wrapper, text=label, text_color=Theme.MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        combo = ctk.CTkComboBox(wrapper, values=values, variable=variable, **input_style())
        combo.grid(row=0, column=1, sticky="ew")
        return combo

    def _slider_card(self, title, specs, row, column, rowspan=1):
        card = SliderCard(
            self.scroll,
            title,
            specs,
            self.app.tk_controls,
            self.app.calibration_data,
            self.app.on_slider_value,
        )
        card.grid(row=row, column=column, rowspan=rowspan, sticky="nsew", padx=Theme.ROW_GAP // 2, pady=Theme.ROW_GAP // 2)
        return card

    def refresh_source_options(self):
        cameras = self.app.tk_controls.get("DETECTED_CAMERAS", [])
        self.sources = [f"Camera {c}" for c in cameras] + get_video_files_from_folder()

    def refresh_com_options(self):
        self.com_ports = SerialCommunicator.list_available_ports()

    def update_sources(self):
        current_lane = self.lane_source.get()
        current_object = self.object_source.get()
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
            self.app.show_status("No sources found", "warning")
            return
        self.lane_combo.configure(values=self.sources)
        self.object_combo.configure(values=self.sources)

    def update_coms(self):
        self.refresh_com_options()
        self.security_combo.configure(values=self.com_ports)
        self.sender_combo.configure(values=self.com_ports)
        if not self.com_ports:
            self.app.show_status("No COM ports found", "warning")

    def apply_sources(self):
        lane = self._clean_source(self.lane_combo.get())
        obj = self._clean_source(self.object_combo.get())
        self.app.tk_controls.lane_source = lane
        self.app.tk_controls.object_source = obj
        self.app.settings_store.update({"LANE_SOURCE": lane, "OBJECT_SOURCE": obj}, DEFAULT_UI_PATH)
        self.app.show_status("Sources applied", "success")

    def apply_coms(self):
        sender = self.sender_combo.get()
        security = self.security_combo.get()
        self.app.shared_controls.send_data = bool(sender) and sender in self.com_ports
        self.app.shared_controls.sender_com = sender
        self.app.shared_controls.security_com = security
        self.app.settings_store.update({"SENDER_COM": sender, "SECURITY_COM": security}, DEFAULT_UI_PATH)
        self.app.show_status("COM ports applied", "success")

    def sync_dynamic_ranges(self):
        max_height = self.app.shared_controls.get("MAX_HEIGHT")
        if isinstance(max_height, (int, float)) and max_height > 0:
            control = self.extras_card.controls.get("Lines")
            if control and control.spec.max_value != max_height:
                control.spec = SliderSpec("Lines", "Lines", 0, max_height)
                control.slider.configure(to=max_height, number_of_steps=max(1, int(max_height)))

    @staticmethod
    def _clean_source(value):
        return value.replace("Camera ", "") if value.startswith("Camera ") else value

    @staticmethod
    def _display_source(value):
        return f"Camera {value}" if str(value).isdigit() else value


class ManualView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=Theme.BG)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
        scroll.grid_columnconfigure((0, 1), weight=1, uniform="manual")

        self.video = VideoTile(scroll, "Manual Video", "Waiting for manual frame", "lane")
        self.video.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        source_card = Card(scroll, "Manual Source", accent=Theme.SECONDARY)
        source_card.grid(row=1, column=0, sticky="new", padx=6, pady=6)
        source_card.grid_columnconfigure(0, weight=1)

        sources = [f"Camera {c}" for c in self.app.tk_controls.get("DETECTED_CAMERAS", [])] + get_video_files_from_folder()
        default = self._display_source(self.app.init_data.get("LANE_SOURCE_TAB2", ""))
        self.source_var = ctk.StringVar(value=default)
        self.source_combo = ctk.CTkComboBox(source_card, values=sources, variable=self.source_var, **input_style())
        self.source_combo.grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        row = ctk.CTkFrame(source_card, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        row.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(row, text="Apply", **button_style(True), command=self.apply_source).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ctk.CTkButton(row, text="Refresh", **button_style(), command=self.refresh_sources).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        self.control_card = SliderCard(
            scroll,
            "Manual Control",
            [
                SliderSpec("MANUAL_DIRECTION", "Direction", 0, 180),
                SliderSpec("MANUAL_SPEED", "Speed", 0, 255),
            ],
            self.app.tk_controls,
            self.app.calibration_data,
            self._manual_slider_changed,
            accent=Theme.SECONDARY,
        )
        self.control_card.grid(row=1, column=1, sticky="new", padx=6, pady=6)

        self.wheel_card = Card(scroll, "Steering Wheel", accent=Theme.SECONDARY)
        self.wheel_card.grid(row=2, column=0, columnspan=2, sticky="n", padx=6, pady=6)
        self.wheel = ctk.CTkCanvas(self.wheel_card, width=170, height=170, bg=Theme.PANEL, highlightthickness=0)
        self.wheel.grid(row=1, column=0, padx=24, pady=(0, 20))
        self.wheel.bind("<B1-Motion>", self._wheel_drag)
        self._draw_wheel(self.app.tk_controls.get("MANUAL_DIRECTION", 90))

    def apply_source(self):
        selected = self._clean_source(self.source_combo.get())
        self.app.tk_controls.lane_source_tab2 = selected
        self.app.shared_controls["LANE_SOURCE_TAB2"] = selected
        self.app.settings_store.update({"LANE_SOURCE_TAB2": selected}, DEFAULT_UI_PATH)
        self.app.show_status("Manual source applied", "success")

    def refresh_sources(self):
        current = self.source_combo.get()
        exclude = []
        if current.startswith("Camera "):
            try:
                exclude.append(int(current.replace("Camera ", "")))
            except ValueError:
                pass
        sources = [f"Camera {i}" for i in detect_camera_indices(exclude_indices=exclude)] + get_video_files_from_folder()
        if not sources:
            self.app.show_status("No manual sources found", "warning")
            return
        self.source_combo.configure(values=sources)

    def sync_car_info(self):
        data = self.app.shared_controls.car_info
        direction = data.get("CAR_DIRECTION_DATA")
        speed = data.get("CAR_SPEED_DATA")
        if direction is not None:
            self.control_card.set_value("MANUAL_DIRECTION", direction)
            self._draw_wheel(direction)
        if speed is not None:
            self.control_card.set_value("MANUAL_SPEED", speed)

    def _manual_slider_changed(self, key, value):
        self.app.tk_controls[key] = value
        lane_data = {
            "CAR_SPEED_DATA": self.app.tk_controls.get("MANUAL_SPEED", 0),
            "CAR_DIRECTION_DATA": self.app.tk_controls.get("MANUAL_DIRECTION", 0),
        }
        self.app.shared_controls.car_info = lane_data
        if key == "MANUAL_DIRECTION":
            self._draw_wheel(value)

    def _draw_wheel(self, angle):
        self.wheel.delete("all")
        cx = cy = 85
        radius = 68

        self.wheel.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius, outline=Theme.SECONDARY, width=3
        )
        for tick_angle in range(0, 181, 30):
            rad = np.deg2rad(tick_angle - 90)
            x1 = cx + (radius - 8) * np.cos(rad)
            y1 = cy + (radius - 8) * np.sin(rad)
            x2 = cx + (radius + 1) * np.cos(rad)
            y2 = cy + (radius + 1) * np.sin(rad)
            self.wheel.create_line(x1, y1, x2, y2, fill=Theme.BORDER_HOVER, width=2)

        self.wheel.create_oval(
            cx - 28, cy - 28, cx + 28, cy + 28, fill=Theme.PANEL_ALT, outline=Theme.BORDER_HOVER, width=1
        )

        radians = np.deg2rad(float(angle) - 90)
        x = cx + radius * 0.75 * np.cos(radians)
        y = cy + radius * 0.75 * np.sin(radians)
        self.wheel.create_line(cx, cy, x, y, fill=Theme.SECONDARY, width=4, capstyle="round")
        self.wheel.create_oval(x - 7, y - 7, x + 7, y + 7, fill=Theme.SECONDARY, outline=Theme.PANEL_ALT, width=2)

    def _wheel_drag(self, event):
        dx = event.x - 85
        dy = event.y - 85
        angle = int((np.rad2deg(np.arctan2(dy, dx)) + 90) % 180)
        self.control_card.controls["MANUAL_DIRECTION"].set(angle)

    @staticmethod
    def _clean_source(value):
        return value.replace("Camera ", "") if value.startswith("Camera ") else value

    @staticmethod
    def _display_source(value):
        return f"Camera {value}" if str(value).isdigit() else value


class TaskManagerView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG)
        self.active = False
        self.job = None
        self.compact = ctk.BooleanVar(value=False)
        self.metric = ctk.StringVar(value="Memory")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = Card(self, "Task Manager")
        card.grid(row=0, column=0, sticky="nsew", padx=18, pady=14)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)
        card.grid_rowconfigure(4, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        header.grid_columnconfigure(0, weight=1)
        self.summary = ctk.CTkLabel(header, text="Waiting for data...", text_color=Theme.MUTED, font=font_caption())
        self.summary.grid(row=0, column=0, sticky="w")
        ctk.CTkSwitch(header, text="Compact", variable=self.compact, command=self._toggle_compact).grid(
            row=0, column=1, sticky="e"
        )

        table = ctk.CTkFrame(card, fg_color="transparent")
        table.grid(row=2, column=0, sticky="nsew", padx=16)
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(0, weight=1)
        cols = ("ProcessName", "Id", "Priority", "Memory (MB)")
        self.tree = ttk.Treeview(table, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort(c, False))
            self.tree.column(col, stretch=True, minwidth=50)
        self.tree.tag_configure("evenrow", background=Theme.PANEL_ALT)
        self.tree.tag_configure("oddrow", background=Theme.PANEL_SOFT)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self._configure_tree()

        self.metric_menu = ctk.CTkOptionMenu(
            card,
            values=["Memory", "CPU", "IO"],
            variable=self.metric,
            command=lambda _: self.refresh(),
            fg_color=Theme.PANEL_SOFT,
            button_color=Theme.PANEL_SOFT,
        )
        self.metric_menu.grid(row=3, column=0, sticky="w", padx=16, pady=(10, 0))
        self.fig = Figure(figsize=(5, 2), dpi=100, facecolor=Theme.PANEL)
        self.ax = self.fig.add_subplot(111, facecolor=Theme.PANEL)
        self.canvas = FigureCanvasTkAgg(self.fig, master=card)
        self.canvas.get_tk_widget().grid(row=4, column=0, sticky="nsew", padx=16, pady=(8, 16))

    def set_active(self, active):
        self.active = active
        if active and self.job is None:
            self.after_idle(self.refresh)
        elif not active and self.job is not None:
            self.after_cancel(self.job)
            self.job = None

    def refresh(self):
        self.job = None
        if not self.active:
            return
        data = get_active_python_processes()
        processes = data.get("processes", [])
        labels, memory, cpu, io_values = [], [], [], []
        seen: set[str] = set()
        for index, proc in enumerate(processes):
            pid = proc.get("pid")
            iid = str(pid)
            seen.add(iid)
            mem = proc.get("memory_mb", 0.0)
            labels.append(str(pid))
            memory.append(mem)
            cpu.append(proc.get("cpu_percent", 0.0))
            io_values.append(proc.get("io_mb", 0.0))
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            values = (proc.get("name"), pid, proc.get("priority"), f"{mem:.2f}")
            if self.tree.exists(iid):
                self.tree.item(iid, values=values, tags=(tag,))
            else:
                self.tree.insert("", "end", iid=iid, values=values, tags=(tag,))
            self.tree.move(iid, "", index)
        for stale_iid in [item for item in self.tree.get_children() if item not in seen]:
            self.tree.delete(stale_iid)
        self.summary.configure(
            text=(
                f"Python processes: {data.get('process_count', len(processes))} | "
                f"Total RAM: {data.get('total_ram_mb', 0.0):.2f} MB | "
                f"System CPU: {data.get('system_cpu', 0.0):.1f}%"
            )
        )
        self._draw_chart(labels, memory, cpu, io_values)
        self.job = self.after(2000, self.refresh)

    def _draw_chart(self, labels, memory, cpu, io_values):
        metric = self.metric.get()
        values = memory if metric == "Memory" else cpu if metric == "CPU" else io_values
        xlabel = "MB" if metric == "Memory" else "% CPU" if metric == "CPU" else "I/O MB"
        self.ax.clear()
        self.ax.set_facecolor(Theme.PANEL)
        self.fig.patch.set_facecolor(Theme.PANEL)
        if values:
            self.ax.barh(labels, values, color=Theme.PRIMARY, edgecolor=Theme.PRIMARY_HOVER, height=0.6)
            self.ax.grid(axis="x", color=Theme.BORDER, linestyle="--", linewidth=0.6, alpha=0.7)
            self.ax.set_axisbelow(True)
        else:
            self.ax.text(0.5, 0.5, "No Python processes found", color=Theme.MUTED, ha="center")
        self.ax.set_xlabel(xlabel, color=Theme.MUTED, fontsize=9)
        self.ax.tick_params(axis="x", colors=Theme.MUTED, labelsize=8)
        self.ax.tick_params(axis="y", colors=Theme.TEXT, labelsize=8)
        for spine_name in ("top", "right", "left"):
            self.ax.spines[spine_name].set_visible(False)
        self.ax.spines["bottom"].set_color(Theme.BORDER)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _toggle_compact(self):
        if self.compact.get():
            self.metric_menu.grid_remove()
            self.canvas.get_tk_widget().grid_remove()
        else:
            self.metric_menu.grid()
            self.canvas.get_tk_widget().grid()

    def _sort(self, col, descending):
        rows = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]
        try:
            rows.sort(reverse=descending, key=lambda x: float(x[0]))
        except ValueError:
            rows.sort(reverse=descending, key=lambda x: x[0].lower())
        for index, item in enumerate(rows):
            self.tree.move(item[1], "", index)
        self.tree.heading(col, command=lambda: self._sort(col, not descending))

    def _configure_tree(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background=Theme.PANEL_ALT,
            fieldbackground=Theme.PANEL_ALT,
            foreground=Theme.TEXT,
            rowheight=30,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=Theme.PANEL_SOFT,
            foreground=Theme.MUTED,
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", Theme.PRIMARY_SOFT)],
            foreground=[("selected", Theme.TEXT)],
        )


class NavRail(ctk.CTkFrame):
    ITEMS = (
        ("Home", "home", "Home"),
        ("Manual", "manual", "Manual"),
        ("Task Manager", "activity", "Tasks"),
    )

    def __init__(self, master, on_select, on_settings, on_defaults, on_options):
        super().__init__(master, fg_color=Theme.SIDEBAR, corner_radius=0, width=Theme.SIDEBAR_WIDTH)
        self.grid_propagate(False)
        self.grid_rowconfigure(1, weight=1)
        self.on_select = on_select
        self.buttons: dict[str, ctk.CTkButton] = {}
        self.indicators: dict[str, ctk.CTkFrame] = {}

        ctk.CTkLabel(self, image=icon("manual", 26, Theme.PRIMARY), text="").grid(row=0, column=0, pady=(20, 24))

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="n")
        for key, glyph, label in self.ITEMS:
            wrapper = ctk.CTkFrame(nav, fg_color="transparent")
            wrapper.pack(pady=4)
            indicator = ctk.CTkFrame(wrapper, width=3, height=32, corner_radius=2, fg_color="transparent")
            indicator.grid(row=0, column=0, padx=(0, 4))
            button = ctk.CTkButton(
                wrapper,
                text=label,
                image=icon(glyph, 20, Theme.MUTED),
                compound="top",
                font=font_caption(),
                command=lambda k=key: self.on_select(k),
                **nav_button_style(False),
            )
            button.grid(row=0, column=1)
            self.buttons[key] = button
            self.indicators[key] = indicator

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, pady=(0, 18))
        for glyph, command in (
            ("settings", on_settings),
            ("defaults", on_defaults),
            ("options", on_options),
        ):
            ctk.CTkButton(
                footer,
                text="",
                image=icon(glyph, 18, Theme.MUTED),
                command=command,
                **icon_button_style(False),
            ).pack(pady=4)

    def set_active(self, name: str) -> None:
        glyphs = {key: glyph for key, glyph, _ in self.ITEMS}
        for key, button in self.buttons.items():
            active = key == name
            button.configure(
                image=icon(glyphs[key], 20, Theme.TEXT if active else Theme.MUTED),
                **nav_button_style(active),
            )
            self.indicators[key].configure(fg_color=Theme.PRIMARY if active else "transparent")


class DashboardShell(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=Theme.BG)
        self.app = app
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.current = None

        self.nav = NavRail(
            self,
            on_select=self.select,
            on_settings=app.open_settings,
            on_defaults=app.open_defaults,
            on_options=app.open_options,
        )
        self.nav.grid(row=0, column=0, sticky="ns")

        right = ctk.CTkFrame(self, fg_color=Theme.BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(right, fg_color=Theme.PANEL, corner_radius=0, height=60)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(topbar, text="Autonomous Team", font=font_heading(), text_color=Theme.TEXT).grid(
            row=0, column=0, padx=(20, 16), pady=14, sticky="w"
        )
        badges = ctk.CTkFrame(topbar, fg_color="transparent")
        badges.grid(row=0, column=2, sticky="e", padx=20, pady=14)
        self.mode_badge = StatusBadge(badges, "Auto", "info")
        self.mode_badge.pack(side="left", padx=4)
        self.cuda_badge = StatusBadge(badges, "CUDA -", "muted")
        self.cuda_badge.pack(side="left", padx=4)
        self.safety_badge = StatusBadge(badges, "Nominal", "success")
        self.safety_badge.pack(side="left", padx=4)

        self.content = ctk.CTkFrame(right, fg_color=Theme.BG)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.status = StatusBadge(right, "Ready", "muted")
        self.status.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 12))

        self.views = {
            "Home": HomeView(self.content, app),
            "Manual": ManualView(self.content, app),
            "Task Manager": TaskManagerView(self.content),
        }
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")
        self._activate("Manual" if app.shared_controls.manual_mode else "Home")

    def select(self, name):
        if name == "Manual" and not self.app.shared_controls.manual_mode:
            if not ConfirmDialog.ask(
                self.winfo_toplevel(),
                "Enable manual mode",
                "The vehicle will switch to manual driving control.",
                "warning",
            ):
                return
            self.app.set_manual_mode(True)
        elif name == "Home" and self.app.shared_controls.manual_mode:
            if not ConfirmDialog.ask(
                self.winfo_toplevel(),
                "Disable manual mode",
                "The vehicle will return to autonomous control.",
                "info",
            ):
                return
            self.app.set_manual_mode(False)
        self._activate(name)

    def _activate(self, name):
        if self.current == name:
            return
        if self.current == "Task Manager":
            self.views["Task Manager"].set_active(False)
        self.current = name
        self.views[name].tkraise()
        self.nav.set_active(name)
        if name == "Task Manager":
            self.views["Task Manager"].set_active(True)

    def sync_state(self, manual_mode: bool, safe_stop: bool, object_safe_stop: bool) -> None:
        if manual_mode:
            self.mode_badge.set("Manual", "warning")
        else:
            self.mode_badge.set("Auto", "info")
        if safe_stop or object_safe_stop:
            self.safety_badge.set("Safe-stop", "danger")
        else:
            self.safety_badge.set("Nominal", "success")

    def set_cuda_status(self, available: bool, device_name: str) -> None:
        if available:
            self.cuda_badge.set(device_name or "CUDA", "success")
        else:
            self.cuda_badge.set("CPU only", "muted")

    def show_status(self, message, tone="info"):
        tone_map = {"success": "success", "warning": "warning", "error": "danger"}.get(tone, "muted")
        self.status.set(message, tone_map)


class AutodriveApp(ctk.CTk):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.title("Autonomous Team")
        self.configure(fg_color=Theme.BG)
        self.minsize(Theme.MIN_WIDTH, Theme.MIN_HEIGHT)
        self.after(0, self._maximize_window)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.settings_store = default_settings_store
        self.calibration_data = {}
        self.init_data = {}
        self.shared_controls = None
        self.tk_controls = None
        self.shared_frames = None
        self.process_manager = None
        self.processes = []
        self.last_webview = None
        self.last_manual_mode = None
        self.loop_job = None
        self.frame_job = None
        self.persist_jobs = {}

        self.boot = BootView(self)
        self.boot.grid(row=0, column=0, sticky="nsew")
        self.shell = None
        self._start_boot()

    def _maximize_window(self) -> None:
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def _start_boot(self):
        self.initializer, _, _ = create_initializer()

        def task():
            def progress(value):
                messages = {
                    25: "Loading settings",
                    50: "Detecting cameras",
                    75: "Checking serial ports",
                    100: "Finalizing runtime",
                }
                self.after(0, lambda: self.boot.set_progress(value, messages.get(value, "Initializing")))

            try:
                flags = self.initializer.prepare_initial_flags(progress_callback=progress)
            except Exception as exc:  # noqa: BLE001 - boot must surface startup failures.
                self.after(0, lambda: self.boot.show_error(str(exc)))
                return
            self.after(0, lambda: self._finish_boot(flags))

        threading.Thread(target=task, daemon=True).start()

    def _finish_boot(self, user_flags):
        self.boot.show_cuda_status(
            bool(user_flags.get("CUDA_AVAILABLE", False)),
            user_flags.get("CUDA_DEVICE_NAME", "CPU only"),
            user_flags.get("CUDA_STATUS_MESSAGE", ""),
        )
        self.shared_controls, self.tk_controls, self.shared_frames, self.user_flags = create_runtime_state(
            self.manager,
            user_flags,
        )
        self.calibration_data = self.settings_store.load(CALIBRATION_FILE)
        self.init_data = self.settings_store.load(DEFAULT_UI_PATH)
        self.process_manager = build_process_manager(
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            user_flags=user_flags,
        )
        self.processes = self.process_manager.create_backend_processes()

        self.shell = DashboardShell(self, self)
        self.shell.grid(row=0, column=0, sticky="nsew")
        self.shell.tkraise()
        self.shell.set_cuda_status(
            bool(user_flags.get("CUDA_AVAILABLE", False)), user_flags.get("CUDA_DEVICE_NAME", "CPU only")
        )
        self.boot.destroy()
        if not user_flags.get("CUDA_AVAILABLE", False):
            self.show_status(user_flags.get("CUDA_STATUS_MESSAGE", "CUDA is recommended."), "warning")
        self._tick_processes()
        self._tick_frames()

    def _tick_processes(self):
        if not self.shared_controls or not self.shared_controls.is_running():
            self.close()
            return
        current_webview = self.shared_controls.webview
        current_manual_mode = self.shared_controls.manual_mode
        _, self.last_webview = self.process_manager.handle_flask_process(current_webview, self.last_webview)
        _, self.last_manual_mode = self.process_manager.handle_lane_object_processes(current_manual_mode, self.last_manual_mode)
        if current_manual_mode and self.shell:
            self.shell.views["Manual"].sync_car_info()
        if self.shell:
            self.shell.views["Home"].sync_dynamic_ranges()
            self.shell.sync_state(
                current_manual_mode,
                self.shared_controls.safe_stop,
                self.shared_controls.object_safe_stop,
            )
        self.loop_job = self.after(250, self._tick_processes)

    def _tick_frames(self):
        if self.shell:
            active = self.shell.current
            if active == "Home" and not self.tk_controls.manual_mode:
                view = self.shell.views["Home"]
                view.normal_video.update_state(
                    self.shared_frames.normal_frame,
                    webview=self.shared_controls.webview,
                    safe_stop=self.shared_controls.safe_stop,
                )
                view.edges_video.update_state(
                    self.shared_frames.edges_frame,
                    webview=self.shared_controls.webview,
                    safe_stop=self.shared_controls.safe_stop,
                )
                view.object_video.update_state(
                    self.shared_frames.object_frame,
                    webview=self.shared_controls.webview,
                    object_safe_stop=self.shared_controls.object_safe_stop,
                )
            elif active == "Manual" and self.tk_controls.manual_mode:
                self.shell.views["Manual"].video.update_state(self.shared_frames.tab2_frame)
        self.frame_job = self.after(33 if self.shell and self.shell.current in {"Home", "Manual"} else 250, self._tick_frames)

    def on_slider_value(self, key, value):
        self.tk_controls[key] = value
        if key in {"MANUAL_DIRECTION", "MANUAL_SPEED", "Side"}:
            return
        if key in self.persist_jobs:
            self.after_cancel(self.persist_jobs[key])
        self.persist_jobs[key] = self.after(250, lambda k=key, v=value: self._persist_slider(k, v))

    def _persist_slider(self, key, value):
        self.persist_jobs.pop(key, None)
        self.settings_store.update({key: value}, CALIBRATION_FILE)

    def set_manual_mode(self, active):
        self.tk_controls.manual_mode = active
        self.shared_controls.manual_mode = active
        self.settings_store.update({"MANUAL_MD": active}, DEFAULT_UI_PATH)

    def restore_defaults(self):
        self.settings_store.load(DEFAULTS_FILE, update_target_if_exists=self.tk_controls)
        for view_name in ("Home",):
            view = self.shell.views[view_name]
            for card in (view.filter_card, view.warp_card, view.pid_card, view.extras_card, view.object_card):
                for key, value in self.tk_controls.items():
                    card.set_value(key, value)
        self.settings_store.update(self.tk_controls, CALIBRATION_FILE, only_existing_keys=True)
        self.show_status("Defaults restored", "success")

    def open_settings(self):
        specs = [
            SliderSpec("BaseConf", "YOLO Confidence", 0, 10),
            SliderSpec("CustomConf", "Custom YOLO Confidence", 0, 10),
            SliderSpec("SemaforoConf", "Traffic Light YOLO Confidence", 0, 10),
            SliderSpec("Timestamp", "Timestamp", 0, 10),
            SliderSpec("StopDecelerationStep", "Stop Deceleration Step", 1, 100),
            SliderSpec("StopRampInterval", "Stop Ramp Interval (s)", 0.0, 1.0, 0.05),
            SliderSpec("SEMAFORO_StopDecelerationStep", "Traffic Light Stop Deceleration Step", 1, 100),
            SliderSpec("SEMAFORO_StopRampInterval", "Traffic Light Stop Ramp Interval (s)", 0.0, 1.0, 0.05),
            SliderSpec("DeviationCounter", "Deviation Counter", 0, 5),
        ]
        modal = self._modal("Settings")
        SliderCard(modal, "Settings", specs, self.tk_controls, self.calibration_data, self.on_slider_value).pack(
            fill="both", expand=True, padx=12, pady=12
        )

    def open_defaults(self):
        modal = self._modal("Defaults")
        card = Card(modal, "Defaults")
        card.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkButton(card, text="Save default", **button_style(True), command=lambda: self._save_defaults(modal)).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(4, 8)
        )
        ctk.CTkButton(card, text="Restore default", **button_style(), command=lambda: self._restore_defaults_modal(modal)).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 16)
        )

    def open_options(self):
        modal = self._modal("Options")
        card = Card(modal, "Options")
        card.pack(fill="both", expand=True, padx=12, pady=12)
        labels = ["WEBVIEW", "SHOW_ROI", "SHOW_INFO", "SEND_LOGS", "NEW_PID", "SHOW_LINES"]
        for index, label in enumerate(labels):
            var = ctk.BooleanVar(value=bool(self.tk_controls.get(label, False)))
            checkbox = ctk.CTkCheckBox(
                card,
                text=label,
                variable=var,
                command=lambda k=label, v=var: self._set_option(k, v.get()),
            )
            checkbox.grid(row=1 + index // 2, column=index % 2, sticky="w", padx=16, pady=8)

    def _set_option(self, key, value):
        self.tk_controls[key] = value
        self.shared_controls[key] = value

    def _save_defaults(self, modal):
        self.settings_store.update(self.tk_controls, DEFAULTS_FILE, only_existing_keys=True)
        modal.destroy()
        self.show_status("Default saved", "success")

    def _restore_defaults_modal(self, modal):
        self.restore_defaults()
        modal.destroy()

    def _modal(self, title):
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.configure(fg_color=Theme.BG)
        modal.transient(self)
        modal.grab_set()
        return modal

    def show_status(self, message, tone="info"):
        if self.shell:
            self.shell.show_status(message, tone)

    def close(self):
        for job in (self.loop_job, self.frame_job, *self.persist_jobs.values()):
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        if self.shared_controls:
            self.shared_controls.webview = False
            self.shared_controls.manual_mode = False
            self.shared_controls.request_shutdown()
        if self.process_manager:
            terminate_runtime_processes(self.processes, self.process_manager)
        self.destroy()


def launch_application(manager):
    app = AutodriveApp(manager)
    app.mainloop()
