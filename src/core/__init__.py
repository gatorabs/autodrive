from src.infrastructure.adapters.calibration.calibration_repository import load_data
from src.infrastructure.utils.setup_flags_processor import prepare_initial_flags, init_shared_controls, print_initial_flags

import multiprocessing as mp
import time

from src.infrastructure.adapters.web_server.app import start_flask_server
from src.application.services.process_service import create_processes, handle_flask_process
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULTS_FILE
from src.infrastructure.logging.logger import Logger