import tkinter as tk
from utils.constants import track_flags as defaults

def create_responsive_interface(tk_controls, frame_width=640, frame_height=480):
    root = tk.Tk()
    root.title("Interface de Controle Unificada")
    root.geometry("1000x600")

    for key, value in defaults.items():
        tk_controls.setdefault(key, value)

    vars = {}

    def toggle_flag(key):
        tk_controls[key] = not tk_controls[key]
        # Atualiza o botão para refletir o novo estado

    # Função para criar e vincular um IntVar/DoubleVar a um controle do manager.dict()
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

    # Frame principal
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    for i in range(4):
        main_frame.columnconfigure(i, weight=1)
    for i in range(2):
        main_frame.rowconfigure(i, weight=1)

    def create_section(title, row, col, colspan=1):
        frame = tk.LabelFrame(main_frame, text=title, padx=10, pady=10)
        frame.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        return frame

    # Toggles
    flags_frame = create_section("Toggles de Visualização", 0, 0)
    for key in ["SHOW_VIDEO", "SHOW_EDGES", "SHOW_ROI", "SHOW_PERSON_DETECTION"]:
        btn = tk.Button(flags_frame, text=f"Toggle {key}",
                        command=lambda k=key: toggle_flag(k))
        btn.pack(anchor="w", fill="x", pady=2)

    # Filtros
    filter_frame = create_section("Parâmetros de Filtragem", 0, 1)
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(key, "int")
        scale = tk.Scale(filter_frame, label=key, from_=0, to=400, orient="horizontal",
                         variable=vars[key])
        scale.pack(fill="x")

    # PID
    pid_frame = create_section("Parâmetros de Controle (PID)", 0, 2)
    pid_params = {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}
    for key, (min_val, max_val) in pid_params.items():
        vars[key] = create_trackbar_var(key, "float")
        scale = tk.Scale(pid_frame, label=key, from_=min_val, to=max_val, resolution=0.001, orient="horizontal",
                         variable=vars[key])
        scale.pack(fill="x")

    # Extras
    extras_frame = create_section("Extras", 0, 3)
    for key, limit in [("Speed", 255), ("Side", 1)]:
        vars[key] = create_trackbar_var(key, "int")
        scale = tk.Scale(extras_frame, label=key, from_=0, to=limit, orient="horizontal",
                         variable=vars[key])
        scale.pack(fill="x")

    # ROI Principal
    roi_main_frame = create_section("ROI da Imagem Principal", 1, 0, colspan=2)
    for key in ["ROI_START", "ROI_END", "ROI_X_START", "ROI_X_END"]:
        max_val = frame_height if "Y" in key else frame_width
        vars[key] = create_trackbar_var(key, "int")
        scale = tk.Scale(roi_main_frame, label=key, from_=0, to=max_val, orient="horizontal",
                         variable=vars[key])
        scale.pack(fill="x")

    # ROI Objetos
    roi_obj_frame = create_section("ROI para Objetos", 1, 2, colspan=2)
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(key, "int")
        scale = tk.Scale(roi_obj_frame, label=key, from_=0, to=240, orient="horizontal",
                         variable=vars[key])
        scale.pack(fill="x")

    root.mainloop()
