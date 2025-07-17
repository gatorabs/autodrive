from src.infrastructure.adapters.display.ui.components.trackbars import create_section
from tkinter import ttk

def build_calibration_section(main_frame, save_fn, restore_fn, save_default_fn):
    calib_frame = create_section(main_frame, "Gerenciar Calibração", 2, 0, colspan=5)
    ttk.Button(calib_frame, text="Salvar Calibração", command=save_fn).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Restaurar Padrão", command=restore_fn).pack(side="left", expand=True, fill="x", padx=5, ipady=10)
    ttk.Button(calib_frame, text="Salvar Novo Padrão", command=save_default_fn).pack(side="left", expand=True, fill="x", padx=5, ipady=10)