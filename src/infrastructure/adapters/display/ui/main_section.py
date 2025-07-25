import json

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import io
from src.infrastructure.adapters.calibration.calibration_repository import load_data, save_data, refresh_json
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULT_UI_PATH, DEFAULTS_FILE
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

        self.com_ports = SerialCommunicator.list_available_ports()
        self.detected_cameras = self.tk_controls.get("DETECTED_CAMERAS", [])
        self._build_ui()

    def _get_valid_com(self, port_name):
        return port_name if port_name in self.com_ports else (self.com_ports[0] if self.com_ports else "")

    def _build_ui(self):
        ctk.CTkLabel(self, text="Fontes e Comunicação", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self._create_source_comboboxes()
        self._create_source_buttons()
        self._create_com_comboboxes()
        self._create_com_buttons()

    def _create_source_comboboxes(self):
        sources = self.detected_cameras + get_video_files_from_folder()

        self.lane_source_combo = self._create_combo_row("Lane Source", sources, self.init_data.get("LANE_SOURCE"))
        self.object_source_combo = self._create_combo_row("Object Source", sources, self.init_data.get("OBJECT_SOURCE"))

    def _create_source_buttons(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=(5, 10))

        ctk.CTkButton(row, text="Aplicar", width=148, command=self.apply_sources).pack(side="left", padx=10)
        ctk.CTkButton(row, text="Atualizar", width=148, command=self.refresh_sources).pack(side="left", padx=10)

    def _create_com_comboboxes(self):
        self.security_com_combo = self._create_combo_row("Security COM", self.com_ports,
                                                         self._get_valid_com(self.shared_controls.get("SECURITY_COM")))
        self.sender_com_combo = self._create_combo_row("Sender COM", self.com_ports,
                                                       self._get_valid_com(self.shared_controls.get("SENDER_COM")))

    def _create_com_buttons(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=(5, 10))

        ctk.CTkButton(row, text="Aplicar", width=148, command=self.apply_sender_com).pack(side="left", padx=10)
        ctk.CTkButton(row, text="Atualizar", width=148, command=self.refresh_com_ports).pack(side="left", padx=10)

    def _create_combo_row(self, label_text, values, default_value):
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(row, text=label_text).pack(side="left", padx=(10, 5))
        combo = ctk.CTkComboBox(row, values=values, variable=ctk.StringVar(value=default_value))
        combo.pack(side="left", fill="x", expand=True)
        return combo

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
        new_options = [f"Câmera {i}" for i in cameras] + videos

        if not new_options:
            return

        self.lane_source_combo.configure(values=new_options)
        self.object_source_combo.configure(values=new_options)

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

class ObjectRoiSection(SliderSection):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            ("Person", "Person", 0, 300),
            ("Traffic", "Traffic Sign", 0, 300)
        ]
        super().__init__(master, "ROI de Objetos", tk_controls, calibration_data, sliders, **kwargs)

class FloatingWidget(ctk.CTkFrame):
    def __init__(self, master, tk_controls, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        # posiciona o widget no canto inferior esquerdo da área de conteúdo
        self.place(relx=1.0, rely=1.0, anchor="se", x=-1087, y=-20)

        self.save_data = save_data
        self.load_data = load_data
        self.tk_controls = tk_controls
        self.DEFAULTS_FILE = DEFAULTS_FILE
        self.button_colors = "#2b2b2b"

        self.modal = None
        self.modal_open = False
        self.modal_width = 0

        # dimensões do modal
        self.max_width = 267
        self.max_height = 40

        self.floating_button = ctk.CTkButton(
            self,
            text="📂",
            width=40,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            command=self.toggle_modal,
        )
        self.floating_button.pack()

    def toggle_modal(self):
        if self.modal_open:
            self._start_closing()
        else:
            self._start_opening()

    def _start_opening(self):
        if self.modal:
            self.modal.destroy()

        self.modal = ctk.CTkFrame(self.master, fg_color="#2b2b2b", corner_radius=0, border_width=2, border_color="#FFFFFF")
        self.modal.place(relx=1.0, rely=1.0, anchor="sw", x=-1080, y=-20)
        self.modal.place_configure(width=0, height=self.max_height)

        btn_frame = ctk.CTkFrame(self.modal, fg_color="#2b2b2b")
        btn_frame.pack(fill="both", expand=True, padx=5)
        self.button1 = ctk.CTkButton(
            btn_frame, text="Salvar Padrão",
            command=self.button_1_action, text_color="#1DBF08", border_color="#1DBF08", border_width=2, fg_color=self.button_colors,
            width=125, height=self.max_height,
        )
        self.button2 = ctk.CTkButton(
            btn_frame, text="Restaurar Padrão",
            command=self.button_2_action,
            width=125, height=self.max_height, text_color="#BF081D", border_color="#BF081D", border_width=2,fg_color=self.button_colors
        )
        self.button1.pack(side="left", padx=(3, 5), pady=5)
        self.button2.pack(side="left", padx=(5, 3), pady=5)

        self.modal_width = 0
        self.modal_open = True
        self._animate_open()

    def _animate_open(self):
        if not self.modal:
            return
        if self.modal_width < self.max_width:
            self.modal_width += 10
            self.modal.place_configure(width=self.modal_width)
            self.after(10, self._animate_open)

    def _start_closing(self):
        # antes de fechar, remove os botões pra não "quebrar" o layout
        if hasattr(self, "button1"):
            self.button1.pack_forget()
            self.button2.pack_forget()
        self._animate_close()

    def _animate_close(self):
        if not self.modal:
            return
        if self.modal_width > 0:
            self.modal_width -= 10
            self.modal.place_configure(width=self.modal_width)
            self.after(10, self._animate_close)
        else:
            self.modal.destroy()
            self.modal = None
            self.modal_open = False

    def button_1_action(self):
        refresh_json(self.tk_controls, self.DEFAULTS_FILE, only_existing_keys=True)
        self._start_closing()

    def button_2_action(self):
        self.master.restore_defaults()  # type: ignore[attr-defined]
        self._start_closing()


class TabManager(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(5, 0))
        self.tabs, self.buttons = {}, {}
        self.left = ctk.CTkFrame(self, fg_color="transparent")
        self.left.pack(side="left", fill="x", expand=True)
        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.right.pack(side="right")
        self.active = None

    def create_tab(self, name, frame, on_right=False):
        def cb():
            self.select_tab(name)
        btn = ctk.CTkButton(
            self.right if on_right else self.left,
            text=name,
            command=cb,
            width=80, height=28,
            fg_color="transparent",
            hover_color="#444444",
            text_color="#fff"
        )
        btn.pack(side="left", padx=5)
        self.buttons[name] = btn
        self.tabs[name] = frame
        if frame:
            frame.grid_forget()
        if self.active is None and frame:
            self.select_tab(name)

    def select_tab(self, name):
        if self.active:
            # esconde antiga
            prev = self.tabs.get(self.active)
            if prev:
                prev.grid_forget()

        # mostra nova
        frm = self.tabs.get(name)
        if frm:
            frm.grid(row=1, column=0, columnspan=3, sticky="nsew")
            self.active = name


class MainApp(ctk.CTk):
    def __init__(self, shared_frames, tk_controls, shared_controls):
        super().__init__()
        self.calibration_data = load_data(CALIBRATION_FILE)
        self.init_data = load_data(DEFAULT_UI_PATH)
        self.title("Visualizador de Frames com Filtros")

        self.DEFAULTS_FILE = DEFAULTS_FILE
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.shared_controls = shared_controls

        self.VIDEO_WIDTH = FRAME_WIDTH_T
        self.VIDEO_HEIGHT = FRAME_HEIGHT_T

        self.GAP = 20
        EXTRA_MARGIN = 20

        self.video_section_height = self.VIDEO_HEIGHT + 12 + EXTRA_MARGIN
        self.warp_section_height = 300
        self.filters_section_height = 110
        self.coms_section_height = 250

        self.filters_coms_section_height = self.filters_section_height + self.coms_section_height + 5

        lower = max(self.warp_section_height, self.filters_coms_section_height) + EXTRA_MARGIN

        self.TOTAL_HEIGHT = self.video_section_height + lower + 50  # + espaço p/ tabs
        self.TOTAL_WIDTH = self.VIDEO_WIDTH*3 + self.GAP*4

        self.geometry(f"{self.TOTAL_WIDTH}x{self.TOTAL_HEIGHT}")
        self.minsize(self.TOTAL_WIDTH, self.TOTAL_HEIGHT)

        # configura grid principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0,1,2), weight=1)

        # cria gerenciador de tabs
        self.tab_manager = TabManager(self)
        # frame Home
        self.home_frame = ctk.CTkFrame(self)
        # frame Tab 2
        self.tab2_frame = ctk.CTkFrame(self)
        ctk.CTkLabel(self.tab2_frame, text="Teste", font=ctk.CTkFont(size=20)).pack(expand=True)

        # registra abas
        self.tab_manager.create_tab("Home",  self.home_frame, on_right=False)
        self.tab_manager.create_tab("Tab 2", self.tab2_frame, on_right=True)

        # monta conteúdo da aba Home **dentro** de self.home_frame
        self._build_home(self.home_frame)
        self.floating_widget = FloatingWidget(self, self.tk_controls)

        # inicia loop
        self.update_loop()

    def _build_home(self, parent):
        # ajusta parent para grid
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=0)
        parent.grid_columnconfigure((0,1,2), weight=1)

        # Vídeos
        nf = VideoFrame(parent, "NORMAL_FRAME"); nf.grid(row=0,column=0,padx=10,pady=(10,2))
        ef = VideoFrame(parent, "EDGES_FRAME");  ef.grid(row=0,column=1,padx=10,pady=(10,2))
        of = VideoFrame(parent, "OBJECT_FRAME");of.grid(row=0,column=2,padx=10,pady=(10,2))
        self.normal_frame, self.edges_frame, self.object_frame = nf, ef, of

        # Warp Controls
        warp_ct = ctk.CTkFrame(parent, width=self.VIDEO_WIDTH, height=300, fg_color="transparent")
        warp_ct.grid(row=1,column=0,rowspan=2,pady=(0,5),sticky="n")
        warp_ct.pack_propagate(False)
        self.warp_controls = WarpControls(warp_ct, self.tk_controls, self.calibration_data)
        self.warp_controls.pack(fill="both",expand=True)

        # Filter Controls
        filt_ct = ctk.CTkFrame(parent, width=self.VIDEO_WIDTH, height=110, fg_color="transparent")
        filt_ct.grid(row=1,column=1,pady=(0,5),sticky="n")
        filt_ct.pack_propagate(False)
        self.filters = FilterControls(filt_ct, self.tk_controls, self.calibration_data)
        self.filters.pack(fill="both",expand=True)

        # Serial Controls
        ser_ct = ctk.CTkFrame(parent, width=self.VIDEO_WIDTH, height=250, fg_color="transparent")
        ser_ct.grid(row=2,column=1,pady=(0,5),sticky="n")
        ser_ct.pack_propagate(False)
        self.sources_controls = SourceAndSerialControls(
            ser_ct, self.tk_controls, self.calibration_data,
            self.shared_controls, self.init_data
        )
        self.sources_controls.pack(fill="both",expand=True)

        # ROI Controls
        roi_ct = ctk.CTkFrame(parent, width=self.VIDEO_WIDTH, height=110, fg_color="transparent")
        roi_ct.grid(row=1,column=2,pady=(0,5),sticky="n")
        roi_ct.pack_propagate(False)
        self.object_roi_controls = ObjectRoiSection(roi_ct, self.tk_controls, self.calibration_data)
        self.object_roi_controls.pack(fill="both",expand=True)

    def update_loop(self):
        try:
            self.normal_frame.update_image(self.shared_frames.get("NORMAL_FRAME"))
            self.edges_frame.update_image(self.shared_frames.get("EDGES_FRAME"))
            self.object_frame.update_image(self.shared_frames.get("OBJECT_FRAME"))
        except Exception as e:
            print("Erro ao atualizar frames:", e)
        self.after(33, self.update_loop)

    def restore_defaults(self):
        load_data(self.DEFAULTS_FILE, update_target_if_exists=self.tk_controls)
        for name, value in self.tk_controls.items():
            # Tenta atualizar cada grupo de sliders
            for section in [self.filters, self.warp_controls, self.object_roi_controls]:
                if name in section.sliders:
                    section.set(name, value)
        refresh_json(self.tk_controls, CALIBRATION_FILE, only_existing_keys=True)

def launch_homepage(shared_frames, tk_controls, shared_controls):
    app = MainApp(shared_frames, tk_controls, shared_controls)
    app.resizable(False, False)
    app.mainloop()
