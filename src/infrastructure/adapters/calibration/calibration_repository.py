import json
import os
from src.infrastructure.logging.logger import Logger

logger = Logger("CalibrationUI", verbose=True)

def save_data(data, file_path):
    if not data:
        logger.warning(
            f"Nenhum dado encontrado.")
        return
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def filter_flags(data, flags_to_ignore):
    return {k: v for k, v in data.items() if k not in flags_to_ignore}


def refresh_json(updates: dict, path: str):
    try:
        with open(path, 'r') as f:
            current_data = json.load(f)
    except Exception as e:
        logger.error(f"Falha ao carregar {path}: {e}")
        current_data = {}

    current_data.update(updates)
    save_data(current_data, path)