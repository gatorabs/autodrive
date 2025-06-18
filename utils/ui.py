import tkinter as tk
from tkinter import ttk
from utils.constants import RED, RESET, YELLOW, GREEN
from utils.calibration_io import save_calibration


def create_responsive_interface(tk_controls, frame_width=640, frame_height=480):
    root = tk.Tk()
    root.title("Interface de Controle Unificada")
    root.geometry("1000x700")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TScale", sliderthickness=12)

    vars = {}

    def toggle_flag(key):
        tk_controls[key] = not tk_controls[key]

    def create_trackbar_var(key, var_type="int"):
        if var_type == "float":
            var = tk.DoubleVar(value=tk_controls[key])
        else:
            var = tk.IntVar(value=tk_controls[key])

        def on_var_change(*args):
            val = var.get()
            tk_controls[key] = val

        var.trace_add("write", on_var_change)
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

        def update_label(*args):
            value_label.config(text=f"{var.get():.3f}" if isinstance(var.get(), float) else str(var.get()))

        var.trace_add("write", update_label)

    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def save_calibration_data():
        try:
            controls_copy = dict(tk_controls)
            calib_data = {k: v for k, v in controls_copy.items() if isinstance(v, (int, float, bool))}
            save_calibration(calib_data)
            print(f"{YELLOW}[UI]{RESET}{GREEN}[INFO] Calibração salva com sucesso.{RESET}")
        except Exception as e:
            print(f"{YELLOW}[UI]{RESET}{RED}[ERROR] Erro na calibração: {e}.{RESET}")

    for i in range(4):
        main_frame.columnconfigure(i, weight=1)
    for i in range(5):
        main_frame.rowconfigure(i, weight=1)

    def restore_defaults():
        from utils.constants import track_flags
        for key, val in track_flags.items():
            tk_controls[key] = val
            if key in vars:
                vars[key].set(val)
        save_calibration(dict(track_flags))
        print(f"{YELLOW}[UI]{RESET}{GREEN}[INFO] Calibração setada em Default.{RESET}")

    def create_section(title, row, col, colspan=1):
        frame = ttk.LabelFrame(main_frame, text=title, padding=(10, 5))
        frame.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        return frame

    flags_frame = create_section("Toggles de Visualização", 0, 0)
    for key in ["SHOW_VIDEO", "SHOW_EDGES", "SHOW_ROI", "SHOW_PERSON_DETECTION"]:
        btn = ttk.Button(flags_frame, text=f"Toggle {key}", command=lambda k=key: toggle_flag(k))
        btn.pack(anchor="w", fill="x", pady=2)

    filter_frame = create_section("Parâmetros de Filtragem", 0, 1)
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(filter_frame, key, vars[key], 0, 400)

    pid_frame = create_section("Parâmetros de Controle (PID)", 0, 2)
    pid_params = {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}
    for key, (min_val, max_val) in pid_params.items():
        vars[key] = create_trackbar_var(key, "float")
        create_trackbar_row(pid_frame, key, vars[key], min_val, max_val)

    extras_frame = create_section("Extras", 0, 3)
    for key, limit in [("Speed", 255), ("Side", 1)]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(extras_frame, key, vars[key], 0, limit)

    roi_main_frame = create_section("ROI da Imagem Principal", 1, 0, colspan=2)
    for key in ["ROI_START", "ROI_END", "ROI_X_START", "ROI_X_END"]:
        max_val = frame_height if "Y" in key else frame_width
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(roi_main_frame, key, vars[key], 0, max_val)

    roi_obj_frame = create_section("ROI para Objetos", 1, 2, colspan=2)
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(key, "int")
        create_trackbar_row(roi_obj_frame, key, vars[key], 0, 240)

    warp_top = create_section("Warp Top Points", 2, 0, colspan=2)
    for pt in ["tl", "tr"]:
        for axis in ["x", "y"]:
            key = f"{pt}_{axis}"
            max_val = frame_width if axis == "x" else frame_height
            vars[key] = create_trackbar_var(key, "int")
            create_trackbar_row(warp_top, key, vars[key], 0, max_val)

    warp_bottom = create_section("Warp Bottom Points", 2, 2, colspan=2)
    for pt in ["bl", "br"]:
        for axis in ["x", "y"]:
            key = f"{pt}_{axis}"
            max_val = frame_width if axis == "x" else frame_height
            vars[key] = create_trackbar_var(key, "int")
            create_trackbar_row(warp_bottom, key, vars[key], 0, max_val)

    calibration_frame = create_section("Gerenciar Calibração", 3, 0, colspan=4)
    calibration_frame.configure(height=60)

    ttk.Button(calibration_frame, text="Salvar Calibração", command=save_calibration_data).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calibration_frame, text="Restaurar Padrão", command=restore_defaults).pack(side="left", expand=True, fill="x", padx=5, ipady=10)

    root.mainloop()
