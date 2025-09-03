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

def load_data(file_path, update_target_if_exists=None):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                loaded = json.load(f)

                if update_target_if_exists is not None:
                    for key, value in loaded.items():
                        if key in update_target_if_exists:
                            update_target_if_exists[key] = value
                    return update_target_if_exists  # atualizado em lugar
                return loaded

        except json.JSONDecodeError:
            pass
    return {} if update_target_if_exists is None else update_target_if_exists


def filter_flags(data, flags_to_ignore):
    return {k: v for k, v in data.items() if k not in flags_to_ignore}


def refresh_json(updates: dict, path: str, only_existing_keys: bool = False):
    try:
        with open(path, 'r') as f:
            current_data = json.load(f)
    except Exception as e:
        logger.error(f"Falha ao carregar {path}: {e}")
        current_data = {}

    if only_existing_keys:
        filtered_updates = {k: v for k, v in updates.items() if k in current_data}
        current_data.update(filtered_updates)
    else:
        current_data.update(updates)

    save_data(current_data, path)
