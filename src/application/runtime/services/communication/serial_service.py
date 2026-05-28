from queue import Empty

from src.domain.models.data.lane_data import LaneData
from src.domain.models.data.object_data import ObjectData
from src.domain.services.driving.traffic_light_service import TRAFFIC_LIGHT_GREEN


def sync_object_data_from_queue(manual_md, object_queue, obj_data: ObjectData):
    if manual_md:
        obj_data.custom_object_data = 0
        obj_data.custom_object_label = ""
        obj_data.object_person_data = 0
        obj_data.traffic_light_data = TRAFFIC_LIGHT_GREEN
        while not object_queue.empty():
            try:
                object_queue.get_nowait()
            except Empty:
                break
        return

    try:
        new_obj = object_queue.get_nowait()
        obj_data.update(new_obj)
    except Empty:
        pass


def publish_serial_data(
    lane_data: LaneData,
    obj_data: ObjectData,
    serial_comm,
    logger,
    verbose,
):
    payload = [
        lane_data.car_direction_data,
        lane_data.car_speed_data,
        obj_data.traffic_light_data,
    ]

    if not serial_comm.ensure_connection():
        return

    try:
        serial_comm.send(payload, verbose)
    except Exception as exc:  # pragma: no cover - hardware interaction
        logger.error(f"Falha ao enviar dados: {exc}")
        serial_comm.close()


def change_serial_port(
    new_com,
    current_com,
    serial_comm,
    shared_controls,
    logger=None,
    open_for_receive=False,
):
    if not new_com or new_com == current_com:
        return current_com

    serial_comm.change_port(
        new_port=new_com,
        send_data=shared_controls.get("SEND_DATA", False),
        open_for_receive=open_for_receive,
    )
    if logger:
        logger.info(f"Porta serial alterada: {current_com} -> {new_com}")
    return new_com


__all__ = [
    "sync_object_data_from_queue",
    "publish_serial_data",
    "change_serial_port",
]
