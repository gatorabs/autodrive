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
from src.infrastructure.logging.logger import Logger

FRAME_WIDTH_T = 360
FRAME_HEIGHT_T = 203

logger = Logger("MainUI")

class SliderSection(ctk.CTkFrame):
    def __init__(self, master, title, tk_controls, calibration_data, sliders_config, **kwargs):
        super().__init__(master, **kwargs)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.refresh_json = refresh_json

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self.sliders = {}

        for config in sliders_config:
            if not isinstance(config, tuple):
                raise TypeError(f"Esperado tupla em sliders_config, mas recebeu: {type(config)}")

            if len(config) == 4:
                name, label, min_val, max_val = config
                step = 1
            elif len(config) == 5:
                name, label, min_val, max_val, step = config
            else:
                raise ValueError(f"Tupla inválida em sliders_config: {config}")

            default = self.calibration_data.get(name, self.tk_controls.get(name, min_val))
            slider, value_label = self.add_slider(
                self,
                label_text=label,
                name=name,
                from_=min_val,
                to=max_val,
                default=default,
                step=step
            )
            self.sliders[name] = {"slider": slider, "label": value_label}

    def add_slider(self, parent, label_text, name, from_, to, default, step=1):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=20, pady=2)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=label_text).grid(row=0, column=0, padx=(10, 5))

        num_steps = int(round((to - from_) / step))

        slider = ctk.CTkSlider(
            row,
            from_=from_,
            to=to,
            number_of_steps=num_steps,
            command=lambda value, n=name, s=step, l=label_text: self._on_slider_change(n, value, s)
        )
        slider.set(default)
        slider.grid(row=0, column=1, padx=5, sticky="ew")

        value_label = ctk.CTkLabel(row, text=str(default))
        value_label.grid(row=0, column=2, padx=(5, 10))

        return slider, value_label

    def _on_slider_change(self, name, value, step):
        stepped_value = round(value / step) * step

        # Atualiza visualmente o label
        label = self.sliders[name]["label"]
        if step < 1:
            label.configure(text=f"{stepped_value:.2f}")
        else:
            label.configure(text=str(int(stepped_value)))

        # Atualiza controle e persiste com refresh_json
        self.tk_controls[name] = stepped_value
        self.refresh_json({name: stepped_value}, CALIBRATION_FILE)

    def get(self, name):
        return int(self.sliders[name]["slider"].get())

    def set(self, name, value):
        self.sliders[name]["slider"].set(value)
        self.sliders[name]["label"].configure(text=str(int(value)))
        self.tk_controls[name] = int(value)

class VideoFrame(ctk.CTkFrame):
    def __init__(self, master, shared_controls, title="Frame", **kwargs):
        super().__init__(master, **kwargs)
        self.shared_controls = shared_controls
        self.label = ctk.CTkLabel(self, text=title)
        self.label.pack()

        placeholder_img = Image.new("RGB", (FRAME_WIDTH_T, FRAME_HEIGHT_T), color=(50, 50, 50))
        self.placeholder_ctk_image = CTkImage(light_image=placeholder_img, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))

        self.image_label = ctk.CTkLabel(self, text="", image=self.placeholder_ctk_image)
        self.image_label.pack()

    def update_image(self, image_bytes):
        if self.shared_controls.get("WEBVIEW"):
            self.image_label.configure(image=self.placeholder_ctk_image, text="Webview ATIVO.")
            self.image_label.image = self.placeholder_ctk_image
            return
        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes)).resize((FRAME_WIDTH_T, FRAME_HEIGHT_T))
            ctk_image = CTkImage(light_image=image, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))
            self.image_label.configure(image=ctk_image, text="")
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
            ("Person", "Person", 0, 240),
            ("Traffic", "Traffic Sign", 0, 240),
            ("Ex1", "Extra Object", 0, 10),
            ("Ex2", "Extra Object 2", 0, 10)
        ]
        super().__init__(master, "ROI de Objetos", tk_controls, calibration_data, sliders, **kwargs)

class FloatingWidget(ctk.CTkFrame):
    def __init__(self, master, tk_controls, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        # posiciona o widget no canto inferior esquerdo da área de conteúdo
        self.place(relx=1.0, rely=1.0, anchor="se", x=-700, y=-27)

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
        self.modal.place(relx=1.0, rely=1.0, anchor="sw", x=-693, y=-27)
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

class ExtrasControls(SliderSection):
    def __init__(self, master, tk_controls, calibration_data, shared_controls, **kwargs):
        sliders = [
            ("Lines",    "Lines",    0, FRAME_HEIGHT),
            ("Distance", "Distance", 0, 270),
            ("Speed",    "Speed",    0, 255),
            ("Side",     "Side",     1, 2),
        ]

        super().__init__(master, "Extras", tk_controls, calibration_data, sliders, **kwargs)
        self.checkbox_section = CheckboxSection(
            self,
            labels=["WEBVIEW", "SHOW_ROI", "SHOW_INFO", "SEND_LOGS", "NEW_PID", "MANUAL_MD"],
            tk_controls=self.tk_controls,
            shared_controls=shared_controls,
            orientation="grid",
            columns=3
        )
        self.checkbox_section.pack(fill="x", padx=2, pady=(33, 0))

class CheckboxSection(ctk.CTkFrame):
    def __init__(self, master, labels, tk_controls, shared_controls, orientation="horizontal", columns=2, **kwargs):
        super().__init__(master, **kwargs)
        self.labels = labels
        self.tk_controls = tk_controls
        self.columns = columns
        self.vars = {}
        self.shared_controls = shared_controls
        self.refresh_json = refresh_json

        if orientation == "grid":
            self._create_grid()
        elif orientation == "horizontal":
            self._create_horizontal()
        elif orientation == "vertical":
            self._create_vertical()

    def _create_grid(self):
        for index, label in enumerate(self.labels):
            row = index // self.columns
            col = index % self.columns
            self._create_checkbox(label, row=row, column=col)

    def _create_horizontal(self):
        for label in self.labels:
            self._create_checkbox(label).pack(side="left", padx=10)

    def _create_vertical(self):
        for label in self.labels:
            self._create_checkbox(label).pack(anchor="w", pady=2)

    def _create_checkbox(self, label, row=None, column=None):
        initial_value = self.tk_controls.get(label, False)
        var = ctk.BooleanVar(value=initial_value)
        checkbox = ctk.CTkCheckBox(self, text=label, variable=var, command=self._save_state)
        self.vars[label] = var

        if row is not None and column is not None:
            checkbox.grid(row=row, column=column, padx=10, pady=5, sticky="w")

        return checkbox

    def _save_state(self):
        updates = {}
        for label, var in self.vars.items():
            value = var.get()
            self.tk_controls[label] = value
            if label in ("WEBVIEW", "NEW_PID", "MANUAL_MD"):
                self._save_to_default(label, value)
            else:
                updates[label] = value
        if updates:
            refresh_json(updates, path=CALIBRATION_FILE)

    def _save_to_default(self, key: str, value: bool):
        try:
            self.refresh_json({key: value}, path=DEFAULT_UI_PATH)
            self.shared_controls[key] = value

        except Exception as e:
            logger.error(f"Erro ao salvar em {DEFAULT_UI_PATH}: {e}")

    def get_states(self):
        return {label: var.get() for label, var in self.vars.items()}

class PIDSection(SliderSection):
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders_config = [
            ("KP", "KP", 0.0, 5.0, 0.01),
            ("KI", "KI", 0.0, 10.0, 0.01),
            ("KD", "KD", 0.0, 10.0, 0.01)
        ]
        super().__init__(
            master=master,
            title="PID",
            tk_controls=tk_controls,
            calibration_data=calibration_data,
            sliders_config=sliders_config,
            height=120,
            **kwargs
        )

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
        self.pid_section_height = 165

        self.first_colunm_section_height = self.pid_section_height + self.warp_section_height

        self.object_roi_section_height = 165
        self.extras_section_height = 280

        self.last_colunm_section_height = self.extras_section_height + self.object_roi_section_height

        self.coms_section_height = 250
        self.filters_section_height = 110
        self.filters_coms_section_height = self.filters_section_height + self.coms_section_height + 5

        lower = max(self.first_colunm_section_height, self.filters_coms_section_height, self.last_colunm_section_height) + EXTRA_MARGIN

        self.TOTAL_HEIGHT = self.video_section_height + lower + 30
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

        self.tab_manager.create_tab("Home",  self.home_frame, on_right=False)
        self._build_home(self.home_frame)

        self._build_tab2_frame()
        # inicia loop
        self.update_loop()

    def _build_home(self, parent):
        # === GRID CONFIG ===
        # 2 linhas de controles (0 = vídeos / 1 = toda a área de controles)
        parent.grid_rowconfigure((0, 1), weight=0)
        parent.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

        self.floating_widget = FloatingWidget(self, self.tk_controls)

        # === VÍDEOS (row 0) ===
        VIDEO_WIDTH, VIDEO_HEIGHT = 360, 203

        def _add_video_frame(col, name):
            container = ctk.CTkFrame(parent, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fg_color="transparent")
            container.grid(row=0, column=col, padx=10, pady=(10, 2), sticky="nsew")
            container.grid_propagate(False)
            video = VideoFrame(container, self.shared_controls, name)
            video.pack(expand=True, fill="both")
            return video

        self.normal_frame = _add_video_frame(0, "NORMAL_FRAME")
        self.edges_frame = _add_video_frame(1, "EDGES_FRAME")
        self.object_frame = _add_video_frame(2, "OBJECT_FRAME")

        # === SEÇÕES DE CONTROLE (row 1) ===
        # helper para criar blocos fixos
        def _make_section(master, height, ControlClass, *args):
            sec = ctk.CTkFrame(master, height=height, fg_color="transparent")
            sec.pack(fill="x", pady=5, padx=10)
            sec.pack_propagate(False)
            ctrl = ControlClass(sec, *args)
            ctrl.pack(expand=True, fill="both")
            return ctrl

        # Coluna 0: Warp em cima e PID embaixo, em dois containers
        col0 = ctk.CTkFrame(parent, fg_color="transparent")
        col0.grid(row=1, column=0, sticky="nsew")
        self.warp_controls = _make_section(col0, 300, WarpControls, self.tk_controls, self.calibration_data)
        self.pid_controls = _make_section(col0, 165, PIDSection, self.tk_controls, self.calibration_data)

        # Coluna 1: wrapper que empacota Filtros + Fontes/Serial em sequência
        col1 = ctk.CTkFrame(parent, fg_color="transparent")
        col1.grid(row=1, column=1, sticky="nsew")
        self.filters = _make_section(col1, 110, FilterControls, self.tk_controls, self.calibration_data)
        self.sources_controls = _make_section(col1, 250,
                                              SourceAndSerialControls,
                                              self.tk_controls,
                                              self.calibration_data,
                                              self.shared_controls,
                                              self.init_data
                                              )

        # Coluna 2: wrapper para ROI + Extras
        col2 = ctk.CTkFrame(parent, fg_color="transparent")
        col2.grid(row=1, column=2, sticky="nsew")
        self.object_roi_controls = _make_section(col2, 165, ObjectRoiSection, self.tk_controls, self.calibration_data)
        self.extras_controls = _make_section(col2, 280, ExtrasControls,
                                             self.tk_controls, self.shared_controls, self.shared_controls)

    def _build_tab2_frame(self):
        self.tab2_frame = ctk.CTkFrame(self)

        # registra aba na direita
        self.tab_manager.create_tab("Tab 2", self.tab2_frame, on_right=True)

        # configura layout com 3 colunas
        self.tab2_frame.columnconfigure((0, 1, 2), weight=1)
        self.tab2_frame.rowconfigure(0, weight=0)
        self.tab2_frame.rowconfigure(1, weight=1)

        # adiciona o vídeo na coluna central
        self.central_video_frame_tab2 = VideoFrame(
            master=self.tab2_frame,
            shared_controls=self.shared_controls,
            title="Vídeo Central"
        )
        self.central_video_frame_tab2.grid(
            row=0, column=1, pady=(10, 5), padx=10, sticky="n"
        )

    def update_loop(self):
        try:
            self.normal_frame.update_image(self.shared_frames.get("NORMAL_FRAME"))
            self.edges_frame.update_image(self.shared_frames.get("EDGES_FRAME"))
            self.object_frame.update_image(self.shared_frames.get("OBJECT_FRAME"))
        except Exception as e:
            logger.error("Erro ao atualizar frames:", e)
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
