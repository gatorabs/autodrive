import sys
import ctypes

def enable_windows_dpi_awareness():
    """
    Habilita DPI awareness no Windows para evitar que o sistema
    faça scaling automático dos pixels quando o usuário muda
    a escala de tela (125%, 150%, etc).
    """
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
