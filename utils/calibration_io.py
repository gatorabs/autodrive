import json
import os
from utils.constants import track_flags, YELLOW, RED, RESET

CALIBRATION_FILE = "calibration_data.json"
DEFAULTS_FILE = "defaults.json"

def save_calibration(data):
    with open(CALIBRATION_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_calibration():
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_defaults(data):
    if not data:
        print(
            f"{YELLOW}[CALIBRATION-UI]{RESET}{RED}[WARNING] Tentando Salvar defaults vazios.{RESET}")
        return
    with open(DEFAULTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def load_defaults():
    if os.path.exists(DEFAULTS_FILE):
        try:
            with open(DEFAULTS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"{YELLOW}[CALIBRATION-UI]{RESET}{RED}[WARNING] Nenhum padrão salvo. Usando track_flags originais.{RESET}")
    return dict(track_flags)
