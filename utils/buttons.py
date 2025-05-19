import tkinter as tk
from tkinter import ttk
from processing.priorities_processor import set_process_priority


def create_tkinter_controls(controls):
    set_process_priority("below_normal")
    root = tk.Tk()
    root.title("Controles do Sistema Autônomo")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    # Armazena referências de variáveis
    check_vars = {}
    entry_vars = {}

    # ===== Checkboxes para flags booleanas =====
    def create_checkbox(key):
        var = tk.BooleanVar(value=controls[key])
        check_vars[key] = var

        def on_toggle():
            controls[key] = var.get()
            print(f"{key}: {controls[key]}")

        chk = tk.Checkbutton(frame, text=key, variable=var, command=on_toggle)
        chk.pack(anchor='w', pady=2)

    # ===== Entradas de texto para strings =====
    def create_entry(key):
        var = tk.StringVar(value=controls[key])
        entry_vars[key] = var

        def on_change(*args):
            controls[key] = var.get()
            print(f"{key}: {controls[key]}")

        lbl = tk.Label(frame, text=key)
        lbl.pack(anchor='w')
        entry = tk.Entry(frame, textvariable=var)
        entry.pack(fill='x', pady=2)
        var.trace_add("write", on_change)

    # ===== Botão de emergência =====
    def trigger_emergency_stop():
        controls["EMERGENCY_STOP"] = 1
        print("🛑 EMERGENCY_STOP acionado!")

    # ===== Adiciona os controles na interface =====

    # Booleans
    bool_keys = [
        "SHOW_VIDEO", "SHOW_EDGES", "SHOW_ROI", "SHOW_PERSON_DETECTION",
        "SHOW_FPS", "SEND_DATA", "RUNNING", "WEBVIEW"
    ]
    for key in bool_keys:
        create_checkbox(key)

    # Strings
    create_entry("SECURITY_COM")
    create_entry("SENDER_COM")

    # Botão de emergência
    btn_emergency = tk.Button(frame, text="🔴 EMERGENCY STOP", fg="white", bg="red", command=trigger_emergency_stop)
    btn_emergency.pack(fill='x', pady=10)

    root.mainloop()
