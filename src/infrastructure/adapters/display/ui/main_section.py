import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import io
from src.infrastructure.adapters.calibration.calibration_repository import load_data
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT
from src.infrastructure.adapters.serial.serial_comm import  SerialCommunicator

FRAME_WIDTH_T = 360
FRAME_HEIGHT_T = 203

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

class FilterControls(ctk.CTkFrame):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        ctk.CTkLabel(self, text="Filtros", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        # F_Canny
        f_row = ctk.CTkFrame(self)
        f_row.pack(fill="x", padx=20, pady=2)
        f_row.columnconfigure(1, weight=1)

        ctk.CTkLabel(f_row, text="F_Canny").grid(row=0, column=0, padx=(10, 5))
        self.f_canny_slider = ctk.CTkSlider(f_row, from_=0, to=255, number_of_steps=255, command=self.update_f_canny)
        default_f_canny = self.calibration_data.get("F_Canny", self.tk_controls.get("F_Canny"))
        self.f_canny_slider.set(default_f_canny)
        self.f_canny_slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.f_canny_value = ctk.CTkLabel(f_row, text=str(self.f_canny_slider.get()), fg_color="transparent",
                                          bg_color="transparent")
        self.f_canny_value.grid(row=0, column=2, padx=(5, 10))

        # S_Canny
        s_row = ctk.CTkFrame(self)
        s_row.pack(fill="x", padx=20, pady=2)
        s_row.columnconfigure(1, weight=1)

        ctk.CTkLabel(s_row, text="S_Canny").grid(row=0, column=0, padx=(10, 5))
        self.s_canny_slider = ctk.CTkSlider(s_row, from_=0, to=255, number_of_steps=255, command=self.update_s_canny)
        default_s_canny = self.calibration_data.get("S_Canny", self.tk_controls.get("S_Canny"))
        self.s_canny_slider.set(default_s_canny)
        self.s_canny_slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.s_canny_value = ctk.CTkLabel(s_row, text=str(self.s_canny_slider.get()), fg_color="transparent",
                                          bg_color="transparent")
        self.s_canny_value.grid(row=0, column=2, padx=(5, 10))

    def update_f_canny(self, value):
        value = int(value)
        self.tk_controls["F_Canny"] = value
        self.f_canny_value.configure(text=str(value))

    def update_s_canny(self, value):
        value = int(value)
        self.tk_controls["S_Canny"] = value
        self.s_canny_value.configure(text=str(value))

class WarpControls(ctk.CTkFrame):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data

        ctk.CTkLabel(self, text="Warp Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self.sliders = {}

        points = [
            ("tl_x", FRAME_WIDTH),
            ("tl_y", FRAME_HEIGHT),
            ("tr_x", FRAME_WIDTH),
            ("tr_y", FRAME_HEIGHT),
            ("bl_x", FRAME_WIDTH),
            ("bl_y", FRAME_HEIGHT),
            ("br_x", FRAME_WIDTH),
            ("br_y", FRAME_HEIGHT),
        ]

        for name, max_value in points:
            self._add_slider(name, max_value)

    def _add_slider(self, name, max_value):
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=20, pady=2)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=name).grid(row=0, column=0, padx=(10, 5))
        slider = ctk.CTkSlider(row, from_=0, to=max_value, number_of_steps=max_value, command=lambda v, n=name: self._update_value(n, v))
        default = self.calibration_data.get(name, self.tk_controls.get(name, 0))
        slider.set(default)
        slider.grid(row=0, column=1, padx=5, sticky="ew")

        value_label = ctk.CTkLabel(row, text=str(int(slider.get())), fg_color="transparent", bg_color="transparent")
        value_label.grid(row=0, column=2, padx=(5, 10))

        self.sliders[name] = {
            "slider": slider,
            "label": value_label
        }

    def _update_value(self, name, value):
        value = int(value)
        self.tk_controls[name] = value
        self.sliders[name]["label"].configure(text=str(value))

class SourceAndSerialControls(ctk.CTkFrame):
    def __init__(self, master, tk_controls, calibration_data, shared_controls, **kwargs):
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.shared_controls = shared_controls

        ctk.CTkLabel(self, text="Fontes e Comunicação", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self.com_ports = SerialCommunicator.list_available_ports()

        def get_valid_com(port_name):
            return port_name if port_name in self.com_ports else (self.com_ports[0] if self.com_ports else "")

        # LANE SOURCE
        lane_row = ctk.CTkFrame(self)
        lane_row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(lane_row, text="Lane Source").pack(side="left", padx=(10, 5))
        self.lane_source_combo = ctk.CTkComboBox(
            lane_row,
            values=["camera", "video"],
            variable=ctk.StringVar(value=calibration_data.get("lane_source", "camera"))
        )
        self.lane_source_combo.pack(side="left", fill="x", expand=True)

        # OBJECT SOURCE
        object_row = ctk.CTkFrame(self)
        object_row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(object_row, text="Object Source").pack(side="left", padx=(10, 5))
        self.object_source_combo = ctk.CTkComboBox(
            object_row,
            values=["camera", "video"],
            variable=ctk.StringVar(value=calibration_data.get("object_source", "camera"))
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
        self.tk_controls["LANE_SOURCE"] = lane_value
        self.tk_controls["OBJECT_SOURCE"] = object_value

    def refresh_sources(self):
        print("[INFO] Atualizar fontes: funcionalidade futura")

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
        selected_com = self.sender_com_combo.get()
        self.shared_controls["SENDER_COM"] = selected_com

class MainApp(ctk.CTk):
    def __init__(self, shared_frames, tk_controls, shared_controls):
        super().__init__()
        self.calibration_data = load_data(CALIBRATION_FILE)
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
        self.warp_container.grid(row=1, column=0, rowspan=2, pady=(2, 5), sticky="n")
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
        self.filters.pack(fill="both", expand=False)

        # Seção de Fontes e Seriais (centro - parte inferior)
        self.serials_container = ctk.CTkFrame(self)
        self.serials_container.grid(row=2, column=1, pady=(0, 5), sticky="n")
        self.serials_container.configure(width=self.VIDEO_WIDTH, height=250)
        self.serials_container.pack_propagate(False)

        self.sources_controls = SourceAndSerialControls(self.serials_container, self.tk_controls, self.calibration_data, self.shared_controls)
        self.sources_controls.pack(fill="both", expand=True)

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
    app.mainloop()
