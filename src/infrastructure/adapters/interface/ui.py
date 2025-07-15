import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import cv2
from tkinter.scrolledtext import ScrolledText
from src.infrastructure.constants.video_constants import FRAME_HEIGHT, FRAME_WIDTH
from src.infrastructure.adapters.calibration.config_persistence import save_data, load_data
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULTS_FILE, DEFAULT_UI_PATH
from src.infrastructure.adapters.video.begin_the_video import detect_camera_indices, get_video_files_from_folder


def create_responsive_interface(tk_controls, shared_frames, shared_controls):
    root = tk.Tk()
    root.title("Interface de Controle Unificada")

    webview = shared_controls.get("WEBVIEW")
    if not webview:
        root.geometry("1400x950")
    else:
        root.geometry("1400x600")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TScale", sliderthickness=12)

    vars = {}

    def toggle_flag(key):
        tk_controls[key] = not tk_controls[key]

    def create_trackbar_var(key, var_type="int"):
        if var_type == "float":
            var = tk.DoubleVar(value=tk_controls.get(key, 0.0))
        else:
            var = tk.IntVar(value=tk_controls.get(key, 0))
        var.trace_add("write", lambda *args: tk_controls.__setitem__(key, var.get()))
        return var

    def create_trackbar_row(parent, label_text, var, from_, to, resolution=None):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label_text, width=8).pack(side="left")
        scale = ttk.Scale(row, from_=from_, to=to, orient="horizontal", variable=var)
        if resolution:
            scale.configure(length=200)
        scale.pack(side="left", fill="x", expand=True)
        value_label = ttk.Label(row, text=str(var.get()), width=6)
        value_label.pack(side="left", padx=5)
        var.trace_add("write", lambda *args: value_label.config(
            text=f"{var.get():.3f}" if isinstance(var.get(), float) else str(var.get())
        ))

    # Container principal
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Grade de 5 colunas e linhas automáticas
    for i in range(5):
        main_frame.columnconfigure(i, weight=1)
        main_frame.rowconfigure(i, weight=1)

    # Funções de calibração
    def save_calibration_data():
        try:
            data = {k: v for k, v in dict(tk_controls).items() if isinstance(v, (int, float, bool))}
            save_data(data, CALIBRATION_FILE)
            log_message("Calibração salva.")
        except Exception as e:
            log_message(f"Erro ao salvar calibração: {e}")

    def restore_defaults():
        try:
            defaults = load_data(DEFAULTS_FILE)
            for k, v in defaults.items():
                tk_controls[k] = v
                if k in vars:
                    vars[k].set(v)
            log_message("Defaults restaurados com sucesso.")
        except Exception as e:
            log_message(f"Erro ao restaurar padrão: {e}")

    def save_as_new_defaults():
        try:
            data = {k: v for k, v in dict(tk_controls).items() if isinstance(v, (int, float, bool))}
            save_data(data, DEFAULTS_FILE)
            log_message("Novo padrão salvo em defaults.json.")
        except Exception as e:
            log_message(f"Erro ao salvar novo padrão: {e}")

    # Helper para criar seções
    def create_section(title, row, col, colspan=1):
        frame = ttk.LabelFrame(main_frame, text=title, padding=(10, 5))
        frame.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        return frame

    def make_command(k, v):
        def cmd():
            tk_controls[k] = v.get()
            if k == "SHOW_INFO" and v.get():
                vars["LANE_LOGS"].set(False)
                tk_controls["LANE_LOGS"] = False
            elif k == "LANE_LOGS" and v.get():
                vars["SHOW_INFO"].set(False)
                tk_controls["SHOW_INFO"] = False
        return cmd

    # Linha 0: Toggles, Filtragem, PID, Extras, ROI
    flags_frame = create_section("Toggles", 0, 0)
    checkboxes = [("SHOW_ROI", "Show ROI"), ("SHOW_INFO", "SHOW Info"), ("LANE_LOGS", "Show Lane-Logs")]
    if shared_controls.get("SEND_DATA"):
        checkboxes.append(("SEND_LOGS", "Show Send-Logs"))
    for key, label in checkboxes:
        var = tk.BooleanVar(value=tk_controls.get(key, False))
        vars[key] = var
        ttk.Checkbutton(flags_frame, text=label, variable=var, command=make_command(key, var)).pack(fill="x", pady=2)

    filter_frame = create_section("Parâmetros de Filtragem", 0, 1)
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(filter_frame, key, vars[key], 0, 400)

    pid_frame = create_section("Parâmetros de Controle (PID)", 0, 2)
    for key, (mn, mx) in {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}.items():
        vars[key] = create_trackbar_var(key, "float")
        create_trackbar_row(pid_frame, key, vars[key], mn, mx)

    extras_frame = create_section("Extras", 0, 3)
    for key, lim in [("Speed", 255), ("Side", 1), ("Distance", 250), ("Lines", FRAME_HEIGHT)]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(extras_frame, key, vars[key], 0, lim)

    roi_frame = create_section("ROI para Objetos", 0, 4)
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(roi_frame, key, vars[key], 0, 240)

    # Linha 1: Warp Top e Bottom lado a lado
    warp_container = ttk.Frame(main_frame)
    warp_container.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
    warp_container.columnconfigure(0, weight=1)
    warp_container.columnconfigure(1, weight=1)
    warp_top = ttk.LabelFrame(warp_container, text="Warp Top Points", padding=(10,5))
    warp_top.grid(row=0, column=0, sticky="nsew", padx=(0,5))
    warp_bot = ttk.LabelFrame(warp_container, text="Warp Bottom Points", padding=(10,5))
    warp_bot.grid(row=0, column=1, sticky="nsew", padx=(5,0))
    for pt, frame in [("tl", warp_top), ("tr", warp_top)]:
        for ax in ["x", "y"]:
            key = f"{pt}_{ax}"
            mv = FRAME_WIDTH if ax=='x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)
    for pt, frame in [("bl", warp_bot), ("br", warp_bot)]:
        for ax in ["x", "y"]:
            key = f"{pt}_{ax}"
            mv = FRAME_WIDTH if ax=='x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)

    # Linha 2: Calibração
    calib_frame = create_section("Gerenciar Calibração", 2, 0, colspan=5)
    ttk.Button(calib_frame, text="Salvar Calibração", command=save_calibration_data).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Restaurar Padrão", command=restore_defaults).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Salvar Novo Padrão", command=save_as_new_defaults).pack(side="left", expand=True, fill="x", padx=5, ipady=10)

    # Linha 3: Fontes de Vídeo ou Câmera (seletor)
    source_frame = create_section("Fontes de Vídeo ou Câmera", 3, 0, colspan=5)
    # carrega câmeras detectadas do arquivo de defaults
    defaults_ui = load_data(DEFAULT_UI_PATH)
    detected_cameras = defaults_ui.get("DETECTED_CAMERAS", [])
    raw_sources = get_video_files_from_folder("resources/test_videos") + detected_cameras
    combined = [
        os.path.normpath(item) if isinstance(item, str) and not item.isdigit() else item
        for item in raw_sources
    ]

    def create_source_selector(name):
        row = ttk.Frame(source_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{name}:", width=16).pack(side="left")
        # monta mapas de label <-> path
        path_to_label = {}
        label_to_path = {}
        labels = []
        for item in combined:
            label = f"Camera {item}" if (
                        isinstance(item, int) or (isinstance(item, str) and item.isdigit())) else os.path.basename(item)
            path_to_label[item] = label
            label_to_path[label] = item
            labels.append(label)

        combo = ttk.Combobox(row, values=labels, width=40, state="readonly")
        # valor padrão sem disparar evento
        default = tk_controls.get(name, "")
        norm = (default if (isinstance(default, int) or (isinstance(default, str) and default.isdigit()))
                else os.path.normpath(str(default)))
        default_label = path_to_label.get(norm, labels[0] if labels else "")
        if default_label in labels:
            combo.current(labels.index(default_label))
        combo.pack(side="left", fill="x", expand=True)

        def on_select(event, n=name, ltp=label_to_path):
            sel = combo.get()
            val = ltp.get(sel)
            tk_controls[n] = int(val) if isinstance(val, str) and val.isdigit() else val

        combo.bind("<<ComboboxSelected>>", on_select)

    create_source_selector("LANE_SOURCE")
    create_source_selector("OBJECT_SOURCE")

    # Linha 4: Vídeos horizontal (se webview False)
    if not webview:
        video_sec = ttk.LabelFrame(main_frame, text="Exibição de Vídeo / Edges / Object")
        video_sec.grid(row=4, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
        video_sec.columnconfigure((0,1,2), weight=1)
        lbl_v = ttk.Label(video_sec)
        lbl_e = ttk.Label(video_sec)
        lbl_o = ttk.Label(video_sec)
        lbl_v.grid(row=0, column=0)
        lbl_e.grid(row=0, column=1)
        lbl_o.grid(row=0, column=2)

        def to_tk(img):
            if img is None:
                return None
            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        def update_display():
            try:
                if "NORMAL_FRAME" in shared_frames:
                    img = cv2.imdecode(np.frombuffer(shared_frames["NORMAL_FRAME"], np.uint8), cv2.IMREAD_COLOR)
                    i = to_tk(img)
                    lbl_v.config(image=i)
                    lbl_v.image = i
                if "EDGES_FRAME" in shared_frames:
                    img = cv2.imdecode(np.frombuffer(shared_frames["EDGES_FRAME"], np.uint8), cv2.IMREAD_COLOR)
                    j = to_tk(img)
                    lbl_e.config(image=j)
                    lbl_e.image = j
                if "OBJECT_FRAME" in shared_frames:
                    img = cv2.imdecode(np.frombuffer(shared_frames["OBJECT_FRAME"], np.uint8), cv2.IMREAD_COLOR)
                    k = to_tk(img)
                    lbl_o.config(image=k)
                    lbl_o.image = k
            except Exception as e:
                log_message(f"Erro ao atualizar imagens: {e}")
            root.after(50, update_display)

        update_display()

    # Linha 5: Logs de Calibração
    logs_frame = ttk.LabelFrame(main_frame, text="Logs de Calibração", padding=(10, 5))
    logs_frame.grid(row=5, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
    logs_frame.rowconfigure(0, weight=1)
    logs_frame.columnconfigure(0, weight=1)
    log_text = ScrolledText(logs_frame, height=4, state='disabled', wrap='word')
    log_text.grid(row=0, column=0, sticky='nsew')

    def log_message(message):
        log_text['state'] = 'normal'
        log_text.insert('end', message + '\n')
        log_text['state'] = 'disabled'
        log_text.see('end')

    def clear_logs():
        log_text['state'] = 'normal'
        log_text.delete('1.0', 'end')
        log_text['state'] = 'disabled'

    clear_btn = ttk.Button(logs_frame, text="Limpar Logs", command=clear_logs)
    clear_btn.grid(row=1, column=0, sticky='e', pady=5)

    root.mainloop()