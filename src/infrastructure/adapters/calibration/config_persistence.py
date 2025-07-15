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

