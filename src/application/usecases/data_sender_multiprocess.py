import time
from queue import Empty

from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.logging.logger import Logger
from src.infrastructure.services.data_sender_service import (
    publish_emergency_stop,
    publish,
    handle_object_queue,
    change_serial_port,
)
from src.domain.models.LaneData import LaneData
from src.domain.models.ObjectData import ObjectData
from src.infrastructure.utils.priorities_processor import set_process_priority

def data_sender_process(lane_queue,
                        object_queue,
                        shared_controls,
                        tk_controls,
                        verbose=True):

    set_process_priority("high")
    logger = Logger("SerialCommunicator", verbose=verbose)
    current_com = shared_controls.get("SENDER_COM")

    serial_comm = SerialCommunicator(
        com_port=current_com,
        send_data=shared_controls.get("SEND_DATA", False),
        logger=logger
    )

    lane_data = LaneData()
    obj_data = ObjectData()

    send_interval = 0.01
    last_send = time.monotonic()

    try:
        while shared_controls.get("RUNNING", True):
            new_com = shared_controls.get("SENDER_COM")
            current_com = change_serial_port(
                new_com=new_com,
                current_com=current_com,
                serial_comm=serial_comm,
                shared_controls=shared_controls,
                logger=logger,
                open_for_receive=False,
            )

            now = time.monotonic()
            remaining = send_interval - (now - last_send)

            if remaining < 0:
                remaining = 0

            try:
                new_lane = lane_queue.get(timeout=remaining)
                lane_data.update(new_lane)
            except Empty:
                pass

            handle_object_queue(manual_md=shared_controls.get("MANUAL_MD"),
                                object_queue=object_queue,
                                obj_data=obj_data)

            publish_emergency_stop(obj_data=obj_data,
                                   shared_controls=shared_controls,
                                   lane_data=lane_data)

            publish(obj_data=obj_data,
                    lane_data=lane_data,
                    serial_comm=serial_comm,
                    logger=logger,
                    verbose=tk_controls.get("SEND_LOGS"))

            last_send = now

    except Exception as e:
        logger.error(f"Erro inesperado no loop: {e}")
    finally:
        serial_comm.close()
        logger.warning("Comunicação serial encerrada.")
