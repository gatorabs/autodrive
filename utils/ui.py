import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import cv2
from utils.constants import RED, RESET, YELLOW, GREEN, FRAME_WIDTH, FRAME_HEIGHT, track_flags
from utils.calibration_io import save_calibration, save_defaults, load_defaults

def create_responsive_interface(tk_controls, shared_frames, shared_controls):
    root = tk.Tk()
    root.title("Interface de Controle Unificada")

    webview = shared_controls.get("WEBVIEW")
    if not webview:
        root.geometry("1500x800")
    else:
        root.geometry("1000x600")

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
            save_calibration(data)
            print(f"{YELLOW}[UI]{RESET}{GREEN}Calibração salva.{RESET}")
        except Exception as e:
            print(f"{YELLOW}[UI]{RESET}{RED}Erro ao salvar calibração: {e}{RESET}")

    def restore_defaults():
        try:
            defaults = load_defaults()
            if defaults == dict(track_flags):
                save_defaults(defaults)
            for k, v in defaults.items():
                tk_controls[k] = v
                if k in vars:
                    vars[k].set(v)
            print(f"{YELLOW}[UI]{RESET}{GREEN}[INFO] Defaults restaurados com sucesso.{RESET}")
        except Exception as e:
            print(f"{YELLOW}[UI]{RESET}{RED}[ERROR] Erro ao restaurar padrão: {e}{RESET}")

    def save_as_new_defaults():
        try:
            data = {k: v for k, v in dict(tk_controls).items() if isinstance(v, (int, float, bool))}
            save_defaults(data)
            print(f"{YELLOW}[UI]{RESET}{GREEN}Novo padrão salvo em defaults.json.{RESET}")
        except Exception as e:
            print(f"{YELLOW}[UI]{RESET}{RED}Erro ao salvar novo padrão: {e}{RESET}")

    # Helper para criar seções
    def create_section(title, row, col, colspan=1):
        frame = ttk.LabelFrame(main_frame, text=title, padding=(10, 5))
        frame.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        return frame

    # Linha 0: 5 seções lado a lado
    # Toggles
    flags_frame = create_section("Toggles de Visualização", 0, 0)
    for key in ["SHOW_ROI"]:
        ttk.Button(flags_frame, text=f"Toggle {key}", command=lambda k=key: toggle_flag(k)).pack(fill="x", pady=2)
    # Filtragem
    filter_frame = create_section("Parâmetros de Filtragem", 0, 1)
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(filter_frame, key, vars[key], 0, 400)
    # PID
    pid_frame = create_section("Parâmetros de Controle (PID)", 0, 2)
    for key, (mn, mx) in {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}.items():
        vars[key] = create_trackbar_var(key, "float")
        create_trackbar_row(pid_frame, key, vars[key], mn, mx)
    # Extras
    extras_frame = create_section("Extras", 0, 3)
    for key, lim in [("Speed", 255), ("Side", 1), ("Distance", 250), ("Lines", FRAME_HEIGHT)]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(extras_frame, key, vars[key], 0, lim)
    # ROI para Objetos
    roi_frame = create_section("ROI para Objetos", 0, 4)
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(roi_frame, key, vars[key], 0, 240)

    # Linha 1: Warp Top e Bottom lado a lado em container
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
            mv = FRAME_WIDTH if ax == 'x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)
    for pt, frame in [("bl", warp_bot), ("br", warp_bot)]:
        for ax in ["x", "y"]:
            key = f"{pt}_{ax}"
            mv = FRAME_WIDTH if ax == 'x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)

    # Linha 2: Calibração
    calib_frame = create_section("Gerenciar Calibração", 2, 0, colspan=5)
    ttk.Button(calib_frame, text="Salvar Calibração", command=save_calibration_data).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Restaurar Padrão", command=restore_defaults).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Salvar Novo Padrão", command=save_as_new_defaults).pack(
        side="left", expand=True, fill="x", padx=5, ipady=10
    )
    
    # Linha 3: Vídeos horizontal (se webview False)
    if not webview:
        video_sec = ttk.LabelFrame(main_frame, text="Exibição de Vídeo / Edges / Object")
        video_sec.grid(row=3, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
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
                if "display" in shared_frames:
                    img = cv2.imdecode(np.frombuffer(shared_frames["display"], np.uint8), cv2.IMREAD_COLOR)
                    i = to_tk(img)
                    lbl_v.config(image=i)
                    lbl_v.image = i
                if "edges" in shared_frames:
                    img = cv2.imdecode(np.frombuffer(shared_frames["edges"], np.uint8), cv2.IMREAD_COLOR)
                    j = to_tk(img)
                    lbl_e.config(image=j)
                    lbl_e.image = j
                if "object" in shared_frames:
                    img = cv2.imdecode(np.frombuffer(shared_frames["object"], np.uint8), cv2.IMREAD_COLOR)
                    k = to_tk(img)
                    lbl_o.config(image=k)
                    lbl_o.image = k
            except Exception as e:
                print(f"{RED}[UI]{RESET}Erro ao atualizar imagens: {e}")
            root.after(50, update_display)

        update_display()

    root.mainloop()