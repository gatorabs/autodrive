# utils/calibration_io.py
import json
import os

CALIBRATION_FILE = "calibration_data.json"

def save_calibration(data):
    with open(CALIBRATION_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_calibration():
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE, 'r') as f:
            return json.load(f)
    return {}
