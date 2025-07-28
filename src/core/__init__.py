from src.infrastructure.adapters.calibration.calibration_repository import load_data
from src.infrastructure.utils.setup_system_processor import init_shared_controls
from src.infrastructure.adapters.display.init_ui.init_ui_section import init_system
from src.infrastructure.utils.setup_system_processor import prepare_initial_flags, terminate_if_alive

import multiprocessing as mp
import time

from src.infrastructure.adapters.web_server.app import start_flask_server
from src.application.services.process_service import ProcessManager
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULTS_FILE
from src.infrastructure.logging.logger import Logger
