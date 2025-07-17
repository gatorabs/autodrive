
import tkinter as tk
from tkinter import ttk
from src.infrastructure.adapters.calibration.calibration_repository import save_data, load_data, filter_flags
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULTS_FILE
from src.infrastructure.constants.ui_constants.flag_constants import FLAGS_TO_IGNORE
from src.infrastructure.adapters.display.ui.build_sections.trackbars import build_warp_section
from src.infrastructure.adapters.display.ui.build_sections.contents.ui_contents import build_filter_section_content, build_pid_section_content, build_extras_section_content, build_roi_section_content, build_flag_section_content
from src.infrastructure.adapters.display.ui.helpers.ui_helper import ts
from src.infrastructure.adapters.display.ui.build_sections.buttons import build_calibration_section
from src.infrastructure.adapters.display.ui.build_sections.combobox import build_sources_and_serial_section
from src.infrastructure.adapters.display.ui.build_sections.video import build_video_display
from src.infrastructure.adapters.display.ui.build_sections.logging import build_log_section

def create_responsive_interface(tk_controls, shared_frames, shared_controls):
    root = tk.Tk()
    root.title("Interface de Controle Unificada")
    webview = shared_controls.get("WEBVIEW")
    root.geometry("1400x700" if webview else "1400x1020")

    # Configuração de estilo
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TScale", sliderthickness=12)
    style.configure("TFrame", background="#f0f0f0")

    vars = {}
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Configuração do grid principal
    for i in range(5):  # 5 colunas
        main_frame.columnconfigure(i, weight=1)
    for i in range(6):  # 6 linhas
        main_frame.rowconfigure(i, weight=1 if i == 4 else 0)  # Apenas a linha 4 (vídeo) é expansível

    # ========== SEÇÕES SUPERIORES ==========
    # Parâmetros para as seções uniformes
    SECTION_PADX = 5  # Espaçamento horizontal entre seções
    SECTION_PADY = 5  # Espaçamento vertical

    # 1. Seção de Toggles
    flags_frame = ttk.LabelFrame(main_frame, text="Toggles", padding=(10, 5))
    flags_frame.grid(row=0, column=0, sticky="nsew", padx=SECTION_PADX, pady=SECTION_PADY)
    build_flag_section_content(flags_frame, tk_controls, shared_controls, vars)

    # 2. Seção de Filtragem
    filter_frame = ttk.LabelFrame(main_frame, text="Parâmetros de Filtragem", padding=(10, 5))
    filter_frame.grid(row=0, column=1, sticky="nsew", padx=SECTION_PADX, pady=SECTION_PADY)
    build_filter_section_content(filter_frame, tk_controls, vars)

    # 3. Seção de PID
    pid_frame = ttk.LabelFrame(main_frame, text="Parâmetros de Controle (PID)", padding=(10, 5))
    pid_frame.grid(row=0, column=2, sticky="nsew", padx=SECTION_PADX, pady=SECTION_PADY)
    build_pid_section_content(pid_frame, tk_controls, vars)

    # 4. Seção de Extras
    extras_frame = ttk.LabelFrame(main_frame, text="Extras", padding=(10, 5))
    extras_frame.grid(row=0, column=3, sticky="nsew", padx=SECTION_PADX, pady=SECTION_PADY)
    build_extras_section_content(extras_frame, tk_controls, vars)

    # 5. Seção de ROI
    roi_frame = ttk.LabelFrame(main_frame, text="ROI para Objetos", padding=(10, 5))
    roi_frame.grid(row=0, column=4, sticky="nsew", padx=SECTION_PADX, pady=SECTION_PADY)
    build_roi_section_content(roi_frame, tk_controls, vars)

    # ========== SEÇÕES INFERIORES ==========
    # Seção Warp
    build_warp_section(main_frame, tk_controls, vars)

    # Seção de Calibração
    def save_calibration_data():
        try:
            data = {k: v for k, v in dict(tk_controls).items() if isinstance(v, (int, float, bool))}
            save_data(filter_flags(data=data, flags_to_ignore=FLAGS_TO_IGNORE), file_path=CALIBRATION_FILE)
            log_message("Calibração salva.", prefix=ts())
        except Exception as e:
            log_message(f"Erro ao salvar calibração: {e}", "ERROR", prefix=ts())

    def restore_defaults():
        try:
            defaults = load_data(DEFAULTS_FILE)
            for k, v in defaults.items():
                tk_controls[k] = v
                if k in vars:
                    vars[k].set(v)
            log_message("Defaults restaurados com sucesso.", prefix=ts())
        except Exception as e:
            log_message(f"Erro ao restaurar padrão: {e}", "ERROR", prefix=ts())

    def save_as_new_defaults():
        try:
            data = {k: v for k, v in dict(tk_controls).items() if isinstance(v, (int, float, bool))}
            save_data(
                filter_flags(data=data, flags_to_ignore=FLAGS_TO_IGNORE),
                file_path=DEFAULTS_FILE
            )
            log_message("Novo padrão salvo em defaults.json.", prefix=ts())
        except Exception as e:
            log_message(f"Erro ao salvar novo padrão: {e}", "ERROR", prefix=ts())

    build_calibration_section(main_frame, save_calibration_data, restore_defaults, save_as_new_defaults)

    # Seção de Fontes e Portas Seriais
    build_sources_and_serial_section(main_frame, tk_controls, shared_controls)

    # Seção de Logs
    log_message = build_log_section(main_frame)

    # ========== SEÇÃO DE VÍDEO ==========
    video_section = None

    def create_video_section():
        nonlocal video_section
        if video_section is None:
            log_message("Criando exibição embarcada.", prefix=ts())
            video_section = build_video_display(main_frame, shared_frames, shared_controls.get("WEBVIEW"), log_message)

    def destroy_video_section():
        nonlocal video_section
        if video_section is not None:
            log_message("Destruindo exibição embarcada.", "WARNING", prefix=ts())
            log_message("Inicializando WEBVIEW.", prefix=ts())
            video_section.destroy()
            video_section = None

    if not webview:
        create_video_section()

    # ========== CONTROLE DE WEBVIEW ==========
    def update_ui_on_webview_change():
        nonlocal webview, video_section
        current_webview = shared_controls.get("WEBVIEW")
        if current_webview != webview:
            webview = current_webview
            root.geometry("1400x700" if webview else "1400x1020")
            if webview:
                destroy_video_section()
            else:
                log_message("Encerrando WEBVIEW", "WARNING", prefix=ts())
                create_video_section()
        root.after(200, update_ui_on_webview_change)

    update_ui_on_webview_change()
    root.mainloop()