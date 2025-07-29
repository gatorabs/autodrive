import customtkinter as ctk
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.adapters.video.begin_the_video import (
    detect_camera_indices,
    get_video_files_from_folder,
)
from src.infrastructure.adapters.calibration.calibration_repository import refresh_json
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH

class SourceAndSerialControls(ctk.CTkFrame):
    """Manage video sources and serial communication settings."""
    def __init__(self, master, tk_controls, calibration_data, shared_controls, init_data, **kwargs):
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.shared_controls = shared_controls
        self.init_data = init_data
        self.refresh_json = refresh_json

        self.com_ports = SerialCommunicator.list_available_ports()
        self.detected_cameras = self.tk_controls.get("DETECTED_CAMERAS", [])
        self.sources = self.detected_cameras + get_video_files_from_folder()

        self.lane_source_var = ctk.StringVar(value=self.init_data.get("LANE_SOURCE"))
        self.object_source_var = ctk.StringVar(value=self.init_data.get("OBJECT_SOURCE"))
        self.security_com_var = ctk.StringVar(value=self._get_valid_com(self.shared_controls.get("SECURITY_COM")))
        self.sender_com_var = ctk.StringVar(value=self._get_valid_com(self.shared_controls.get("SENDER_COM")))

        self._build_ui()

    def _on_lane_selected(self, _=None):
        self._update_available_sources()

    def _on_object_selected(self, _=None):
        self._update_available_sources()

    def _get_valid_com(self, port_name):
        return port_name if port_name in self.com_ports else (self.com_ports[0] if self.com_ports else "")

    def _build_ui(self):
        ctk.CTkLabel(self, text="Fontes e Comunicação", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self._create_source_comboboxes()
        self._create_source_buttons()
        self._create_com_comboboxes()
        self._create_com_buttons()

    def _create_source_comboboxes(self):
        self.lane_source_combo = self._create_combo_row(
            "Lane Source",
            self.sources,
            self.lane_source_var,
            command=self._on_lane_selected,
        )
        self.object_source_combo = self._create_combo_row(
            "Object Source",
            self.sources,
            self.object_source_var,
            command=self._on_object_selected,
        )

        # remove selected option from the opposite combobox
        self._update_available_sources()

    def _create_source_buttons(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=(5, 10))

        ctk.CTkButton(row, text="Aplicar", width=148, command=self.apply_sources).pack(side="left", padx=10)
        ctk.CTkButton(row, text="Atualizar", width=148, command=self.refresh_sources).pack(side="left", padx=10)

    def _create_com_comboboxes(self):
        self.security_com_combo = self._create_combo_row("Security COM", self.com_ports, self.security_com_var)
        self.sender_com_combo = self._create_combo_row("Sender COM", self.com_ports, self.sender_com_var)

    def _create_com_buttons(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=(5, 10))

        ctk.CTkButton(row, text="Aplicar", width=148, command=self.apply_sender_com).pack(side="left", padx=10)
        ctk.CTkButton(row, text="Atualizar", width=148, command=self.refresh_com_ports).pack(side="left", padx=10)

    def _create_combo_row(self, label_text, values, variable, command=None):
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(row, text=label_text).pack(side="left", padx=(10, 5))
        combo = ctk.CTkComboBox(row, values=values, variable=variable, command=command)
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
            return value.replace("Câmera ", "") if value.startswith("Câmera ") else value

        lane_value = clean_source(self.lane_source_combo.get())
        object_value = clean_source(self.object_source_combo.get())

        self.tk_controls["LANE_SOURCE"] = lane_value
        self.tk_controls["OBJECT_SOURCE"] = object_value

        self.refresh_json({
            "LANE_SOURCE": lane_value,
            "OBJECT_SOURCE": object_value
        }, DEFAULT_UI_PATH)

    def refresh_sources(self):
        cameras = detect_camera_indices()
        videos = get_video_files_from_folder()
        self.sources = [f"Câmera {i}" for i in cameras] + videos

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

        self.shared_controls["SENDER_COM"] = sender_com
        self.shared_controls["SECURITY_COM"] = security_com

        self.refresh_json({
            "SENDER_COM": sender_com,
            "SECURITY_COM": security_com
        }, DEFAULT_UI_PATH)
