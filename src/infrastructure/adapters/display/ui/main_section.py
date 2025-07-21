import json

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import io
from src.infrastructure.adapters.calibration.calibration_repository import load_data, save_data, refresh_json
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULT_UI_PATH
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.adapters.serial.serial_comm import  SerialCommunicator
from src.infrastructure.adapters.video.begin_the_video import detect_camera_indices, get_video_files_from_folder

FRAME_WIDTH_T = 360
FRAME_HEIGHT_T = 203

class SliderSection(ctk.CTkFrame):
    def __init__(self, master, title, tk_controls, calibration_data, sliders_config, **kwargs):
        super().__init__(master, **kwargs)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.refresh_json = refresh_json

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self.sliders = {}
        for config in sliders_config:
            name, label, min_val, max_val = config
            default = self.calibration_data.get(name, self.tk_controls.get(name, 0))
            slider, value_label = self.add_slider(self, label, name, min_val, max_val, default)
            self.sliders[name] = {"slider": slider, "label": value_label}

    def add_slider(self, parent, label_text, name, from_, to, default):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=20, pady=2)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=label_text).grid(row=0, column=0, padx=(10, 5))

        slider = ctk.CTkSlider(
            row,
            from_=from_,
            to=to,
            number_of_steps=to - from_,
            command=lambda value, n=name: self._on_slider_change(n, value)
        )
        slider.set(default)
        slider.grid(row=0, column=1, padx=5, sticky="ew")

        value_label = ctk.CTkLabel(row, text=str(int(default)))
        value_label.grid(row=0, column=2, padx=(5, 10))

        return slider, value_label

    def _on_slider_change(self, name, value):
        int_value = int(float(value))
        self.tk_controls[name] = int_value
        self.sliders[name]["label"].configure(text=str(int_value))
        self.refresh_json({name: int_value}, CALIBRATION_FILE)

    def get(self, name):
        return int(self.sliders[name]["slider"].get())

    def set(self, name, value):
        self.sliders[name]["slider"].set(value)
        self.sliders[name]["label"].configure(text=str(int(value)))
        self.tk_controls[name] = int(value)


class VideoFrame(ctk.CTkFrame):
    def __init__(self, master, title="Frame", **kwargs):
        super().__init__(master, **kwargs)
        self.label = ctk.CTkLabel(self, text=title)
        self.label.pack()
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack()

    def update_image(self, image_bytes):
        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes)).resize((FRAME_WIDTH_T, FRAME_HEIGHT_T))
            ctk_image = CTkImage(light_image=image, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))
            self.image_label.configure(image=ctk_image)
            self.image_label.image = ctk_image

class FilterControls(SliderSection):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            ("F_Canny", "F_Canny", 0, 255),
            ("S_Canny", "S_Canny", 0, 255),
        ]
        super().__init__(master, "Filtros", tk_controls, calibration_data, sliders, **kwargs)

class WarpControls(SliderSection):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        points = [
            ("tl_x", "tl_x", 0, FRAME_WIDTH),
            ("tl_y", "tl_y", 0, FRAME_HEIGHT),
            ("tr_x", "tr_x", 0, FRAME_WIDTH),
            ("tr_y", "tr_y", 0, FRAME_HEIGHT),
            ("bl_x", "bl_x", 0, FRAME_WIDTH),
            ("bl_y", "bl_y", 0, FRAME_HEIGHT),
            ("br_x", "br_x", 0, FRAME_WIDTH),
            ("br_y", "br_y", 0, FRAME_HEIGHT),
        ]
        super().__init__(master, "Warp Controls", tk_controls, calibration_data, points, **kwargs)


class SourceAndSerialControls(ctk.CTkFrame):
    def __init__(self, master, tk_controls, calibration_data, shared_controls, init_data, **kwargs):
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.shared_controls = shared_controls
        self.init_data = init_data
        self.refresh_json = refresh_json

        ctk.CTkLabel(self, text="Fontes e Comunicação", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self.com_ports = SerialCommunicator.list_available_ports()

        def get_valid_com(port_name):
            return port_name if port_name in self.com_ports else (self.com_ports[0] if self.com_ports else "")

        # LANE SOURCE
        lane_row = ctk.CTkFrame(self)
        lane_row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(lane_row, text="Lane Source").pack(side="left", padx=(10, 5))
        detected_cameras = self.tk_controls.get("DETECTED_CAMERAS", [])
        self.lane_source_combo = ctk.CTkComboBox(
            lane_row,
            values=detected_cameras+get_video_files_from_folder(),
            variable=ctk.StringVar(value=self.init_data.get("LANE_SOURCE"))
        )
        self.lane_source_combo.pack(side="left", fill="x", expand=True)

        # OBJECT SOURCE
        object_row = ctk.CTkFrame(self)
        object_row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(object_row, text="Object Source").pack(side="left", padx=(10, 5))
        self.object_source_combo = ctk.CTkComboBox(
            object_row,
            values=detected_cameras+get_video_files_from_folder(),
            variable=ctk.StringVar(value=self.init_data.get("OBJECT_SOURCE"))
        )
        self.object_source_combo.pack(side="left", fill="x", expand=True)

        # Botões para aplicar/atualizar fontes
        source_btn_row = ctk.CTkFrame(self, fg_color="transparent")
        source_btn_row.pack(pady=(5, 10))

        apply_source_btn = ctk.CTkButton(
            source_btn_row,
            text="Aplicar",
            width=148,
            command=self.apply_sources
        )
        apply_source_btn.pack(side="left", padx=10)

        refresh_source_btn = ctk.CTkButton(
            source_btn_row,
            text="Atualizar",
            width=148,
            command=self.refresh_sources  # função placeholder
        )
        refresh_source_btn.pack(side="left", padx=10)

        # SECURITY COM
        security_row = ctk.CTkFrame(self)
        security_row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(security_row, text="Security COM").pack(side="left", padx=(10, 5))
        self.security_com_combo = ctk.CTkComboBox(
            security_row,
            values=self.com_ports,
            variable=ctk.StringVar(value=get_valid_com(shared_controls.get("SECURITY_COM")))
        )
        self.security_com_combo.pack(side="left", fill="x", expand=True)

        # SENDER COM
        sender_row = ctk.CTkFrame(self)
        sender_row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(sender_row, text="Sender COM").pack(side="left", padx=(10, 5))
        self.sender_com_combo = ctk.CTkComboBox(
            sender_row,
            values=self.com_ports,
            variable=ctk.StringVar(value=get_valid_com(shared_controls.get("SENDER_COM"))),
            width=150
        )
        self.sender_com_combo.pack(side="left", fill="x", expand=True)

        com_button_row = ctk.CTkFrame(self, fg_color="transparent")
        com_button_row.pack(pady=(5, 10), anchor="n")

        apply_btn = ctk.CTkButton(com_button_row, text="Aplicar", width=148, command=self.apply_sender_com)
        apply_btn.pack(side="left", padx=10)

        refresh_btn = ctk.CTkButton(com_button_row, text="Atualizar", width=148, command=self.refresh_com_ports)
        refresh_btn.pack(side="left", padx=10)

    def apply_sources(self):
        lane_value = self.lane_source_combo.get()
        object_value = self.object_source_combo.get()

        # Desempacota "Câmera 0" → "0"
        if lane_value.startswith("Câmera "):
            lane_value = lane_value.replace("Câmera ", "")
        if object_value.startswith("Câmera "):
            object_value = object_value.replace("Câmera ", "")

        self.tk_controls["LANE_SOURCE"] = lane_value
        self.tk_controls["OBJECT_SOURCE"] = object_value

        self.refresh_json({
            "LANE_SOURCE": lane_value,
            "OBJECT_SOURCE": object_value
        }, DEFAULT_UI_PATH)

        print("[INFO] LANE_SOURCE e OBJECT_SOURCE atualizados em DEFAULT_UI_PATH.")

    def refresh_sources(self):
        cameras = detect_camera_indices()
        videos = get_video_files_from_folder()

        new_options = [f"Câmera {i}" for i in cameras] + videos

        if not new_options:
            print("[WARNING] Nenhuma fonte de vídeo encontrada.")
            return

        # Atualiza opções nas comboboxes
        self.lane_source_combo.configure(values=new_options)
        self.object_source_combo.configure(values=new_options)

        print(f"[INFO] Fontes atualizadas: {new_options}")

    def refresh_com_ports(self):
        self.com_ports = SerialCommunicator.list_available_ports()
        def refresh_combo(combo, current_value):
            combo.configure(values=self.com_ports)
            if current_value in self.com_ports:
                combo.set(current_value)
            elif self.com_ports:
                combo.set(self.com_ports[0])
            else:
                combo.set("")
        refresh_combo(self.security_com_combo, self.security_com_combo.get())
        refresh_combo(self.sender_com_combo, self.sender_com_combo.get())

    def apply_sender_com(self):
        selected_sender_com = self.sender_com_combo.get()
        selected_security_com = self.security_com_combo.get()
        self.shared_controls["SENDER_COM"] = selected_sender_com
        self.shared_controls["SECURITY_COM"] = selected_security_com
        self.refresh_json({
            "SENDER_COM": selected_sender_com,
            "SECURITY_COM": selected_security_com
        }, DEFAULT_UI_PATH)

class ObjectRoiSection(SliderSection):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            ("Person", "Person", 0, 300),
            ("Traffic", "Traffic Sign", 0, 300)
        ]
        super().__init__(master, "ROI de Objetos", tk_controls, calibration_data, sliders, **kwargs)


class MainApp(ctk.CTk):
    def __init__(self, shared_frames, tk_controls, shared_controls):
        super().__init__()
        self.calibration_data = load_data(CALIBRATION_FILE)
        self.init_data = load_data(DEFAULT_UI_PATH)
        self.title("Visualizador de Frames com Filtros")

        self.VIDEO_WIDTH = FRAME_WIDTH_T
        self.VIDEO_HEIGHT = FRAME_HEIGHT_T
        self.GAP = 20
        EXTRA_MARGIN = 20

        # Alturas individuais
        self.video_section_height = self.VIDEO_HEIGHT + 10 + 2 + EXTRA_MARGIN
        self.warp_section_height = 300
        self.filters_section_height = 110
        self.coms_section_height = 250

        # Novo: empilhamento vertical da coluna central (filtros + COMs)
        self.filters_coms_section_height = self.filters_section_height + self.coms_section_height + 5

        # Altura total
        self.lower_section_height = max(self.warp_section_height, self.filters_coms_section_height) + EXTRA_MARGIN
        self.TOTAL_HEIGHT = self.video_section_height + self.lower_section_height
        self.TOTAL_WIDTH = self.VIDEO_WIDTH * 3 + self.GAP * 4

        # Janela
        self.geometry(f"{self.TOTAL_WIDTH}x{self.TOTAL_HEIGHT}")
        self.minsize(self.TOTAL_WIDTH, self.TOTAL_HEIGHT)
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.shared_controls = shared_controls

        # Layout principal (2 linhas: vídeos e controles)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # -------------------- Seção de Vídeos --------------------
        self.normal_frame = VideoFrame(self, "NORMAL_FRAME")
        self.edges_frame = VideoFrame(self, "EDGES_FRAME")
        self.object_frame = VideoFrame(self, "OBJECT_FRAME")

        self.normal_frame.grid(row=0, column=0, padx=10, pady=(10, 2))
        self.edges_frame.grid(row=0, column=1, padx=10, pady=(10, 2))
        self.object_frame.grid(row=0, column=2, padx=10, pady=(10, 2))

        # Seção de Warp Controls (lado esquerdo)
        self.warp_container = ctk.CTkFrame(self)
        self.warp_container.grid(row=1, column=0, rowspan=2, pady=(0, 5), sticky="n")
        self.warp_container.configure(width=self.VIDEO_WIDTH, height=300)
        self.warp_container.pack_propagate(False)

        self.warp_controls = WarpControls(self.warp_container, self.tk_controls, self.calibration_data)
        self.warp_controls.pack(fill="both", expand=True)

        # Seção de Filtros (centro - parte superior)
        self.filters_container = ctk.CTkFrame(self)
        self.filters_container.grid(row=1, column=1, pady=(0, 5), sticky="n")
        self.filters_container.configure(width=self.VIDEO_WIDTH, height=110)
        self.filters_container.pack_propagate(False)

        self.filters = FilterControls(self.filters_container, self.tk_controls, self.calibration_data)
        self.filters.pack(fill="both", expand=True)

        # Seção de Fontes e Seriais (centro - parte inferior)
        self.serials_container = ctk.CTkFrame(self)
        self.serials_container.grid(row=2, column=1, pady=(0, 5), sticky="n")
        self.serials_container.configure(width=self.VIDEO_WIDTH, height=250)
        self.serials_container.pack_propagate(False)

        self.sources_controls = SourceAndSerialControls(self.serials_container, self.tk_controls, self.calibration_data, self.shared_controls, self.init_data)
        self.sources_controls.pack(fill="both", expand=True)

        # Seção de ROI de Objetos (lado direito abaixo do vídeo)
        self.object_roi_container = ctk.CTkFrame(self)
        self.object_roi_container.grid(row=1, column=2, pady=(0, 5), sticky="n")
        self.object_roi_container.configure(width=self.VIDEO_WIDTH, height=110)
        self.object_roi_container.pack_propagate(False)

        self.object_roi_controls = ObjectRoiSection(self.object_roi_container, self.tk_controls, self.calibration_data)
        self.object_roi_controls.pack(fill="both", expand=True)

        self.update_loop()

    def update_loop(self):
        try:
            self.normal_frame.update_image(self.shared_frames.get("NORMAL_FRAME"))
            self.edges_frame.update_image(self.shared_frames.get("EDGES_FRAME"))
            self.object_frame.update_image(self.shared_frames.get("OBJECT_FRAME"))
        except Exception as e:
            print("Erro ao atualizar frames:", e)

        self.after(33, self.update_loop)  # ~30 FPS


def launch_homepage(shared_frames, tk_controls, shared_controls):
    app = MainApp(shared_frames, tk_controls, shared_controls)
    app.resizable(False, False)
    app.mainloop()
