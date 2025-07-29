import time
from queue import Empty

from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.logging.logger import Logger
from src.application.services.data_sender_service import publish_emergency_stop, publish, switch_serial_com, handle_object_queue