import time
from queue import Empty
from typing import Callable

from src.application.ports import LoggerPort, SerialSender
from src.application.services.serial_pipeline import (
    publish,
    handle_object_queue,
    change_serial_port,
)
from src.domain.services.safety_service import publish_emergency_stop
from src.domain.models.data.object_data import ObjectData
from src.domain.models.data.lane_data import LaneData

def data_sender_process(lane_queue,
                        object_queue,
                        shared_controls,
                        tk_controls,
                        logger_factory: Callable[..., LoggerPort],
                        serial_communicator_factory: Callable[..., SerialSender],
                        priority_setter: Callable[[str], None],
                        verbose=True):

    priority_setter("high")
    logger = logger_factory("SerialCommunicator", verbose=verbose)
    current_com = shared_controls.sender_com

    serial_comm = serial_communicator_factory(
        com_port=current_com,
        send_data=shared_controls.send_data,
        logger=logger
    )

    lane_data = LaneData()
    obj_data = ObjectData()

    send_interval = 0.01
    last_send = time.monotonic()

    try:
        while shared_controls.is_running():
            new_com = shared_controls.sender_com
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

            handle_object_queue(manual_md=shared_controls.manual_mode,
                                object_queue=object_queue,
                                obj_data=obj_data)

            publish_emergency_stop(obj_data=obj_data,
                                   shared_controls=shared_controls,
                                   lane_data=lane_data,
                                   tk_controls=tk_controls)

            publish(obj_data=obj_data,
                    lane_data=lane_data,
                    serial_comm=serial_comm,
                    logger=logger,
                    verbose=tk_controls.send_logs)

            last_send = now

    except Exception as e:
        logger.error(f"Erro inesperado no loop: {e}")
    finally:
        serial_comm.close()
        logger.warning("Comunicação serial encerrada.")
