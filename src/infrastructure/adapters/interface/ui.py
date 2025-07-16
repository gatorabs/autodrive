import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import cv2
from tkinter.scrolledtext import ScrolledText
from src.infrastructure.constants.video_constants import FRAME_HEIGHT, FRAME_WIDTH
from src.infrastructure.adapters.calibration.calibration_repository import save_data, load_data, filter_flags
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULTS_FILE, DEFAULT_UI_PATH
from src.infrastructure.adapters.video.begin_the_video import get_video_files_from_folder, detect_camera_indices
from src.infrastructure.constants.ui_constants.flag_constants import FLAGS_TO_IGNORE
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator

def create_trackbar_var(tk_controls, key, var_type="int"):
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

def create_section(main_frame, title, row, col, colspan=1):
    frame = ttk.LabelFrame(main_frame, text=title, padding=(10, 5))
    frame.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
    return frame

def make_flag_command(tk_controls, vars, k, v, shared_controls=None):
    def cmd():
        tk_controls[k] = v.get()
        if k == "WEBVIEW":
            shared_controls["WEBVIEW"] = v.get()
        if k == "SHOW_INFO" and v.get():
            vars["LANE_LOGS"].set(False)
            tk_controls["LANE_LOGS"] = False
        elif k == "LANE_LOGS" and v.get():
            vars["SHOW_INFO"].set(False)
            tk_controls["SHOW_INFO"] = False
    return cmd

def build_flag_section(main_frame, tk_controls, shared_controls, vars):
    flags_frame = create_section(main_frame, "Toggles", 0, 0)
    checkboxes = [("SHOW_ROI", "Show ROI"), ("SHOW_INFO", "SHOW Info"), ("LANE_LOGS", "Show Lane-Logs"), ("WEBVIEW", "Toggle Webview")]
    if shared_controls.get("SEND_DATA"):
        checkboxes.append(("SEND_LOGS", "Show Send-Logs"))
    for key, label in checkboxes:
        var = tk.BooleanVar(value=tk_controls.get(key, False))
        vars[key] = var
        ttk.Checkbutton(flags_frame, text=label, variable=var, command=make_flag_command(tk_controls, vars, key, var, shared_controls=shared_controls)).pack(fill="x", pady=2)

def build_trackbar_sections(main_frame, tk_controls, vars):
    # Filtragem
    filter_frame = create_section(main_frame, "Parâmetros de Filtragem", 0, 1)
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(filter_frame, key, vars[key], 0, 400)
    # PID
    pid_frame = create_section(main_frame, "Parâmetros de Controle (PID)", 0, 2)
    for key, (mn, mx) in {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}.items():
        vars[key] = create_trackbar_var(tk_controls, key, "float")
        create_trackbar_row(pid_frame, key, vars[key], mn, mx)
    # Extras
    extras_frame = create_section(main_frame, "Extras", 0, 3)
    for key, lim in [("Speed", 255), ("Side", 1), ("Distance", 250), ("Lines", FRAME_HEIGHT)]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(extras_frame, key, vars[key], 0, lim)
    # ROI
    roi_frame = create_section(main_frame, "ROI para Objetos", 0, 4)
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(roi_frame, key, vars[key], 0, 240)

def build_warp_section(main_frame, tk_controls, vars):
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
            vars[key] = create_trackbar_var(tk_controls, key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)
    for pt, frame in [("bl", warp_bot), ("br", warp_bot)]:
        for ax in ["x", "y"]:
            key = f"{pt}_{ax}"
            mv = FRAME_WIDTH if ax=='x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(tk_controls, key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)

def build_calibration_section(main_frame, save_fn, restore_fn, save_default_fn):
    calib_frame = create_section(main_frame, "Gerenciar Calibração", 2, 0, colspan=5)
    ttk.Button(calib_frame, text="Salvar Calibração", command=save_fn).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Restaurar Padrão", command=restore_fn).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Salvar Novo Padrão", command=save_default_fn).pack(side="left", expand=True, fill="x", padx=5, ipady=10)

def build_log_section(main_frame):
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
    return log_message

def build_sources_and_serial_section(main_frame, tk_controls, shared_controls):
    sources_row = ttk.Frame(main_frame)
    sources_row.grid(row=3, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
    sources_row.columnconfigure(0, weight=1, uniform="half")
    sources_row.columnconfigure(1, weight=1, uniform="half")
    sources_row.rowconfigure(0, weight=1)

    # --------- Fontes de Vídeo ou Câmera ----------
    video_frame = ttk.LabelFrame(sources_row, text="Fontes de Vídeo ou Câmera", padding=(10, 5))
    video_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    path_to_label = {}
    label_to_path = {}
    labels = []

    default_lane = tk_controls.get("LANE_SOURCE", "")
    default_obj = tk_controls.get("OBJECT_SOURCE", "")

    def refresh_videos():
        path_to_label.clear()
        label_to_path.clear()
        labels.clear()

        live_cameras = detect_camera_indices(max_tested=2)
        video_files = get_video_files_from_folder("resources/test_videos")

        lane_source = tk_controls.get("LANE_SOURCE", "")
        obj_source = tk_controls.get("OBJECT_SOURCE", "")
        in_use_cameras = set()
        for val in [lane_source, obj_source]:
            if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                in_use_cameras.add(str(val))
        all_cameras = sorted(set(list(live_cameras) + list(in_use_cameras)))

        raw_sources = video_files + all_cameras
        combined = [
            os.path.normpath(item) if isinstance(item, str) and not item.isdigit() else item
            for item in raw_sources
        ]
        for item in combined:
            label = f"Camera {item}" if (
                    isinstance(item, int) or (isinstance(item, str) and item.isdigit())) else os.path.basename(item)
            path_to_label[item] = label
            label_to_path[label] = item
            labels.append(label)
        atualizar_combos()

    def initial_video_sources():
        path_to_label.clear()
        label_to_path.clear()
        labels.clear()
        defaults_ui = load_data(DEFAULT_UI_PATH)
        saved_cameras = defaults_ui.get("DETECTED_CAMERAS", [])
        video_files = get_video_files_from_folder("resources/test_videos")
        raw_sources = video_files + saved_cameras
        combined = [
            os.path.normpath(item) if isinstance(item, str) and not item.isdigit() else item
            for item in raw_sources
        ]
        for item in combined:
            label = f"Camera {item}" if (
                    isinstance(item, int) or (isinstance(item, str) and item.isdigit())) else os.path.basename(item)
            path_to_label[item] = label
            label_to_path[label] = item
            labels.append(label)
        atualizar_combos()

    lane_var = tk.StringVar()
    obj_var = tk.StringVar()

    def atualizar_combos(*_):
        lane_selected = lane_var.get()
        obj_selected = obj_var.get()
        lane_labels = [l for l in labels if l != obj_selected]
        obj_labels = [l for l in labels if l != lane_selected]
        lane_combo['values'] = lane_labels
        obj_combo['values'] = obj_labels
        if lane_var.get() not in lane_labels and lane_labels:
            lane_var.set(lane_labels[0])
        if obj_var.get() not in obj_labels and obj_labels:
            obj_var.set(obj_labels[0])

    # Combobox do LANE_SOURCE
    row1 = ttk.Frame(video_frame)
    row1.pack(fill="x", pady=2)
    ttk.Label(row1, text="LANE_SOURCE:", width=16).pack(side="left")
    lane_combo = ttk.Combobox(row1, textvariable=lane_var, width=30, state="readonly")
    lane_combo.pack(side="left", fill="x", expand=True)

    # Combobox do OBJECT_SOURCE
    row2 = ttk.Frame(video_frame)
    row2.pack(fill="x", pady=2)
    ttk.Label(row2, text="OBJECT_SOURCE:", width=16).pack(side="left")
    obj_combo = ttk.Combobox(row2, textvariable=obj_var, width=30, state="readonly")
    obj_combo.pack(side="left", fill="x", expand=True)

    # Frame horizontal para botões de vídeo (lado a lado, abaixo dos combos)
    video_btns_row = ttk.Frame(video_frame)
    video_btns_row.pack(fill="x", pady=(6, 2))

    refresh_vid_btn = ttk.Button(video_btns_row, text="Atualizar Lista de Vídeos", command=refresh_videos)
    aplicar_vid_btn = ttk.Button(video_btns_row, text="Aplicar Alterações", command=lambda: (
        tk_controls.__setitem__("LANE_SOURCE", int(label_to_path.get(lane_var.get())) if isinstance(label_to_path.get(lane_var.get()), str) and label_to_path.get(lane_var.get()).isdigit() else label_to_path.get(lane_var.get())),
        tk_controls.__setitem__("OBJECT_SOURCE", int(label_to_path.get(obj_var.get())) if isinstance(label_to_path.get(obj_var.get()), str) and label_to_path.get(obj_var.get()).isdigit() else label_to_path.get(obj_var.get()))
    ))
    # Ajusta altura dos botões
    refresh_vid_btn.pack(side="left", fill="x", expand=True, padx=(0, 2), ipady=6)
    aplicar_vid_btn.pack(side="left", fill="x", expand=True, padx=(2, 0), ipady=6)

    lane_var.trace_add("write", atualizar_combos)
    obj_var.trace_add("write", atualizar_combos)

    initial_video_sources()

    norm_lane = (default_lane if (isinstance(default_lane, int) or (isinstance(default_lane, str) and default_lane.isdigit()))
        else os.path.normpath(str(default_lane)))
    norm_obj = (default_obj if (isinstance(default_obj, int) or (isinstance(default_obj, str) and default_obj.isdigit()))
        else os.path.normpath(str(default_obj)))
    lane_label = path_to_label.get(norm_lane, labels[0] if labels else "")
    obj_label = path_to_label.get(norm_obj, labels[0] if labels else "")
    lane_var.set(lane_label)
    obj_var.set(obj_label if obj_label != lane_label else (labels[1] if len(labels) > 1 else labels[0]))

    # --------- Portas Seriais ----------
    serial_frame = ttk.LabelFrame(sources_row, text="Portas Seriais", padding=(10, 5))
    serial_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    def get_defaults():
        defaults_ui = load_data(DEFAULT_UI_PATH)
        return (
            defaults_ui.get("SECURITY_COM", "COM1"),
            defaults_ui.get("SENDER_COM", "COM8"),
        )

    def get_available():
        return SerialCommunicator.list_available_ports()

    default_security, default_sender = get_defaults()
    available_coms = get_available()
    security_var = tk.StringVar(value=default_security if default_security in available_coms else (available_coms[0] if available_coms else ""))
    sender_var   = tk.StringVar(value=default_sender   if default_sender   in available_coms else (available_coms[0] if available_coms else ""))

    row_sec = ttk.Frame(serial_frame)
    row_sec.pack(fill="x", pady=2)
    ttk.Label(row_sec, text="SECURITY_COM:", width=16).pack(side="left")
    sec_combo = ttk.Combobox(row_sec, textvariable=security_var, values=available_coms, width=15, state="readonly")
    sec_combo.pack(side="left", fill="x", expand=True)

    row_send = ttk.Frame(serial_frame)
    row_send.pack(fill="x", pady=2)
    ttk.Label(row_send, text="SENDER_COM:", width=16).pack(side="left")
    send_combo = ttk.Combobox(row_send, textvariable=sender_var, values=available_coms, width=15, state="readonly")
    send_combo.pack(side="left", fill="x", expand=True)

    # Frame horizontal para botões de portas seriais (lado a lado, abaixo dos combos)
    ports_btns_row = ttk.Frame(serial_frame)
    ports_btns_row.pack(fill="x", pady=(6,2))
    refresh_ports_btn = ttk.Button(ports_btns_row, text="Atualizar Lista de Portas", command=lambda: (
        sec_combo.configure(values=get_available()),
        send_combo.configure(values=get_available()),
        security_var.set(get_available()[0] if security_var.get() not in get_available() and get_available() else security_var.get()),
        sender_var.set(get_available()[0] if sender_var.get() not in get_available() and get_available() else sender_var.get())
    ))
    aplicar_ports_btn = ttk.Button(ports_btns_row, text="Aplicar Alterações", command=lambda: (
        tk_controls.__setitem__("SECURITY_COM", security_var.get()),
        tk_controls.__setitem__("SENDER_COM", sender_var.get()),
        shared_controls.__setitem__("SENDER_COM", sender_var.get())
    ))
    refresh_ports_btn.pack(side="left", fill="x", expand=True, padx=(0,2), ipady=6)
    aplicar_ports_btn.pack(side="left", fill="x", expand=True, padx=(2,0), ipady=6)


def build_video_display(main_frame, shared_frames, webview, log_message):
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
        video_sec.after(50, update_display)
    update_display()
    return video_sec

def create_responsive_interface(tk_controls, shared_frames, shared_controls):
    root = tk.Tk()
    root.title("Interface de Controle Unificada")
    webview = shared_controls.get("WEBVIEW")
    root.geometry("1400x800" if webview else "1400x1000")
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TScale", sliderthickness=12)

    vars = {}
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    for i in range(5):
        main_frame.columnconfigure(i, weight=1)
        main_frame.rowconfigure(i, weight=1)

    def save_calibration_data():
        try:
            data = {k: v for k, v in dict(tk_controls).items() if isinstance(v, (int, float, bool))}
            save_data(filter_flags(data=data, flags_to_ignore=FLAGS_TO_IGNORE), file_path=CALIBRATION_FILE)
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
            save_data(
                filter_flags(data=data, flags_to_ignore=FLAGS_TO_IGNORE),
                file_path=DEFAULTS_FILE
            )
            log_message("Novo padrão salvo em defaults.json.")
        except Exception as e:
            log_message(f"Erro ao salvar novo padrão: {e}")

    def update_ui_on_webview_change():
        nonlocal webview, video_section
        current_webview = shared_controls.get("WEBVIEW")
        if current_webview != webview:
            webview = current_webview
            root.geometry("1400x800" if webview else "1400x1000")
            if webview:
                video_section.grid_remove()
            else:
                video_section.grid()
        root.after(200, update_ui_on_webview_change)

    build_flag_section(main_frame, tk_controls, shared_controls, vars)
    build_trackbar_sections(main_frame, tk_controls, vars)
    build_warp_section(main_frame, tk_controls, vars)
    build_calibration_section(main_frame, save_calibration_data, restore_defaults, save_as_new_defaults)
    build_sources_and_serial_section(main_frame, tk_controls, shared_controls)
    log_message = build_log_section(main_frame)
    video_section = build_video_display(main_frame, shared_frames, webview, log_message)

    if webview:
        video_section.grid_remove()
    update_ui_on_webview_change()

    root.mainloop()
