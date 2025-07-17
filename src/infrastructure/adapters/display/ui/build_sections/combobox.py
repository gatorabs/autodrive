from tkinter import ttk
import tkinter as tk
import os
from src.infrastructure.adapters.calibration.calibration_repository import load_data
from src.infrastructure.adapters.video.begin_the_video import detect_camera_indices, get_video_files_from_folder
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH
from src.infrastructure.adapters.display.ui.helpers.ui_helper import save_ui_state, get_available, get_defaults

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
        tk_controls.__setitem__("OBJECT_SOURCE", int(label_to_path.get(obj_var.get())) if isinstance(label_to_path.get(obj_var.get()), str) and label_to_path.get(obj_var.get()).isdigit() else label_to_path.get(obj_var.get())),
        save_ui_state(tk_controls, DEFAULT_UI_PATH)
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
        shared_controls.__setitem__("SENDER_COM", sender_var.get()),
        save_ui_state(tk_controls, DEFAULT_UI_PATH)
    ))
    refresh_ports_btn.pack(side="left", fill="x", expand=True, padx=(0,2), ipady=6)
    aplicar_ports_btn.pack(side="left", fill="x", expand=True, padx=(2,0), ipady=6)