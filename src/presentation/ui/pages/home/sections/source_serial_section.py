import customtkinter as ctk

from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.adapters.video.video_utility_process import (
    detect_camera_indices,
    get_video_files_from_folder,
)
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH
from src.infrastructure.data.repository.calibration_repository import default_settings_store


class SourceAndSerialControls(ctk.CTkFrame):
    """Manage video sources and serial communication settings."""

    def __init__(self, master, tk_controls, calibration_data, shared_controls, init_data, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack_propagate(False)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.shared_controls = shared_controls
        self.init_data = init_data
        self.settings_store = default_settings_store

        self.com_ports = SerialCommunicator.list_available_ports()
        cams = self.tk_controls.get("DETECTED_CAMERAS", [])
        self.detected_cameras = [f"Camera {c}" for c in cams]
        self.sources = self.detected_cameras + get_video_files_from_folder()

        lane_value = self.init_data.get("LANE_SOURCE")
        obj_value = self.init_data.get("OBJECT_SOURCE")
        if str(lane_value).isdigit():
            lane_value = f"Camera {lane_value}"
        if str(obj_value).isdigit():
            obj_value = f"Camera {obj_value}"

        self.lane_source_var = ctk.StringVar(value=lane_value)
        self.object_source_var = ctk.StringVar(value=obj_value)
        self.security_com_var = ctk.StringVar(value=self._get_valid_com(self.shared_controls.security_com))
        self.sender_com_var = ctk.StringVar(value=self._get_valid_com(self.shared_controls.sender_com))

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Entrada e Comunicacao",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w", padx=18, pady=(12, 8))

        self._create_source_comboboxes()
        self._create_com_comboboxes()
        self._create_action_buttons()

    def _on_lane_selected(self, _=None):
        self._update_available_sources()

    def _on_object_selected(self, _=None):
        self._update_available_sources()

    def _get_valid_com(self, port_name):
        return port_name if port_name in self.com_ports else (self.com_ports[0] if self.com_ports else "")

    def _create_source_comboboxes(self):
        self.lane_source_combo = self._create_combo_row(
            "Camera pista",
            self.sources,
            self.lane_source_var,
            command=self._on_lane_selected,
        )
        self.object_source_combo = self._create_combo_row(
            "Camera objetos",
            self.sources,
            self.object_source_var,
            command=self._on_object_selected,
        )
        self._update_available_sources()

    def _create_com_comboboxes(self):
        self.security_com_combo = self._create_combo_row(
            "COM seguranca",
            self.com_ports,
            self.security_com_var,
        )
        self.sender_com_combo = self._create_combo_row(
            "COM envio",
            self.com_ports,
            self.sender_com_var,
        )

    def _create_action_buttons(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(8, 10))

        ctk.CTkButton(
            row,
            text="Fontes",
            width=68,
            height=28,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.apply_sources,
        ).pack(side="left")
        ctk.CTkButton(
            row,
            text="Lista",
            width=68,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.refresh_sources,
        ).pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            row,
            text="COM",
            width=68,
            height=28,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.apply_sender_com,
        ).pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            row,
            text="Portas",
            width=68,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.refresh_com_ports,
        ).pack(side="left", padx=(8, 0))

    def _create_combo_row(self, label_text, values, variable, command=None):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        ctk.CTkLabel(
            row,
            text=label_text,
            width=96,
            anchor="w",
            text_color="#cbd5e1",
        ).pack(side="left", padx=(4, 8))
        combo = ctk.CTkComboBox(
            row,
            values=values,
            variable=variable,
            command=command,
            fg_color="#111827",
            border_color="#334155",
            button_color="#334155",
            button_hover_color="#475569",
        )
        combo.pack(side="left", fill="x", expand=True)
        return combo

    def _update_available_sources(self):
        """Exclude the selected option from the opposite combobox."""
        lane_selected = self.lane_source_var.get()
        obj_selected = self.object_source_var.get()

        lane_options = [s for s in self.sources if s != obj_selected]
        object_options = [s for s in self.sources if s != lane_selected]

        self.lane_source_combo.configure(values=lane_options)
        self.object_source_combo.configure(values=object_options)

        if lane_selected not in lane_options:
            self.lane_source_var.set(lane_options[0] if lane_options else "")
        if obj_selected not in object_options:
            self.object_source_var.set(object_options[0] if object_options else "")

    def apply_sources(self):
        def clean_source(value):
            return value.replace("Camera ", "") if value.startswith("Camera ") else value

        lane_value = clean_source(self.lane_source_combo.get())
        object_value = clean_source(self.object_source_combo.get())

        self.tk_controls.lane_source = lane_value
        self.tk_controls.object_source = object_value

        self.settings_store.update({
            "LANE_SOURCE": lane_value,
            "OBJECT_SOURCE": object_value
        }, DEFAULT_UI_PATH)

    def refresh_sources(self):
        current_lane = self.lane_source_var.get()
        current_object = self.object_source_var.get()

        exclude = []
        for current in (current_lane, current_object):
            if current.startswith("Camera "):
                try:
                    exclude.append(int(current.replace("Camera ", "")))
                except ValueError:
                    continue

        cameras = detect_camera_indices(exclude_indices=exclude)
        videos = get_video_files_from_folder()

        self.sources = [f"Camera {i}" for i in cameras] + videos

        for current in (current_lane, current_object):
            if current.startswith("Camera") and current not in self.sources:
                self.sources.append(current)

        if not self.sources:
            return

        self._update_available_sources()

    def refresh_com_ports(self):
        self.com_ports = SerialCommunicator.list_available_ports()

        def update_combo(combo, current):
            combo.configure(values=self.com_ports)
            if current in self.com_ports:
                combo.set(current)
            elif self.com_ports:
                combo.set(self.com_ports[0])
            else:
                combo.set("")

        update_combo(self.security_com_combo, self.security_com_combo.get())
        update_combo(self.sender_com_combo, self.sender_com_combo.get())

    def apply_sender_com(self):
        sender_com = self.sender_com_combo.get()
        security_com = self.security_com_combo.get()

        valid_sender = bool(sender_com) and sender_com in self.com_ports

        self.shared_controls.send_data = valid_sender
        self.shared_controls.sender_com = sender_com
        self.shared_controls.security_com = security_com

        self.settings_store.update({
            "SENDER_COM": sender_com,
            "SECURITY_COM": security_com
        }, DEFAULT_UI_PATH)
