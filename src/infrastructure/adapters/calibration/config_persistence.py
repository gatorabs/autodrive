import json
import os
from src.infrastructure.logging.logger import Logger

CALIBRATION_FILE = os.path.join("config", "calibration_data.json")
DEFAULTS_FILE    = os.path.join("config", "defaults.json")
logger           = Logger("CalibrationUI", verbose=True)

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
        logger.warning(
            f"Tentando Salvar defaults vazios.")
        return
    with open(DEFAULTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_defaults():
    if os.path.exists(DEFAULTS_FILE):
        try:
            with open(DEFAULTS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Nenhum padrão salvo.")
