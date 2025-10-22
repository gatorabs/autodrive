import time
from queue import Empty

from src.domain.models.lane_data.lane_data import LaneData
from src.domain.models.object_data.object_data import ObjectData
from src.infrastructure.services.object_detection_service import (
    CUSTOM_OBJECT_LABEL_BY_CODE,
)


STOP_SIGN_LABEL = "PLACA_PARE"
DETOUR_LABEL = "PLACA_DESVIO"
LOMBADA_LABEL = "PLACA_LOMBADA"

STOP_SIGN_SPEED_STEP = 10
STOP_SIGN_DECELERATING = "DECELERATING"
STOP_SIGN_HOLDING = "HOLDING"
STOP_SIGN_ACCELERATING = "ACCELERATING"


def _update_car_speed(shared_controls, lane_data, speed):
    lane_data.car_speed_data = speed
    car_info = shared_controls.get("CAR_INFO", {})
    car_info["CAR_SPEED_DATA"] = speed
    shared_controls["CAR_INFO"] = car_info


def _resolve_custom_label(obj_data):
    if getattr(obj_data, "custom_object_label", ""):
        return obj_data.custom_object_label
    return CUSTOM_OBJECT_LABEL_BY_CODE.get(obj_data.custom_object_data, "")


def _approach_speed(shared_controls, lane_data, target_speed, step=STOP_SIGN_SPEED_STEP):
    current_speed = lane_data.car_speed_data
    if current_speed == target_speed:
        return True

    if current_speed < target_speed:
        new_speed = min(target_speed, current_speed + step)
    else:
        new_speed = max(target_speed, current_speed - step)

    if new_speed != current_speed:
        _update_car_speed(shared_controls, lane_data, new_speed)

    return new_speed == target_speed


def _handle_stop_sign_state(shared_controls, lane_data, *, current_time):
    state = shared_controls.get("STOP_SIGN_STATE")

    if state == STOP_SIGN_DECELERATING:
        reached_zero = _approach_speed(shared_controls, lane_data, 0)
        if reached_zero:
            hold_seconds = shared_controls.get("STOP_SIGN_HOLD_SECONDS", 0.0)
            resume_time = current_time + hold_seconds
            shared_controls["STOP_SIGN_RESUME_TIME"] = resume_time
            if hold_seconds > 0:
                shared_controls["STOP_SIGN_STATE"] = STOP_SIGN_HOLDING
            else:
                shared_controls["STOP_SIGN_STATE"] = STOP_SIGN_ACCELERATING
        return True

    if state == STOP_SIGN_HOLDING:
        if lane_data.car_speed_data != 0:
            _update_car_speed(shared_controls, lane_data, 0)
        resume_time = shared_controls.get("STOP_SIGN_RESUME_TIME", current_time)
        if current_time >= resume_time:
            shared_controls["STOP_SIGN_STATE"] = STOP_SIGN_ACCELERATING
        return True

    if state == STOP_SIGN_ACCELERATING:
        target_speed = shared_controls.get("STOP_SIGN_PREV_SPEED", 0)
        if _approach_speed(shared_controls, lane_data, target_speed):
            shared_controls["STOP_SIGN_ACTIVE"] = False
            shared_controls["STOP_SIGN_STATE"] = None
            shared_controls["STOP_SIGN_IGNORE"] = False
            shared_controls.pop("STOP_SIGN_PREV_SPEED", None)
            shared_controls.pop("STOP_SIGN_RESUME_TIME", None)
            shared_controls.pop("STOP_SIGN_HOLD_SECONDS", None)
        return False

    return False


def _get_stop_hold_seconds(tk_controls):
    tk_controls = tk_controls or {}
    try:
        hold_seconds = float(tk_controls.get("Timestamp", 5))
    except (TypeError, ValueError):
        hold_seconds = 5.0
    return max(0.0, hold_seconds)


def publish_emergency_stop(obj_data, shared_controls, lane_data, tk_controls, *, now=None):
    current_time = time.monotonic() if now is None else now

    custom_label = _resolve_custom_label(obj_data)
    hold_seconds = _get_stop_hold_seconds(tk_controls) if custom_label == STOP_SIGN_LABEL else 0.0

    stop_sign_ignore = shared_controls.get("STOP_SIGN_IGNORE", False)
    stop_sign_active = shared_controls.get("STOP_SIGN_ACTIVE", False)

    if (
        not stop_sign_active
        and custom_label == STOP_SIGN_LABEL
        and not stop_sign_ignore
    ):
        shared_controls["STOP_SIGN_ACTIVE"] = True
        shared_controls["STOP_SIGN_STATE"] = STOP_SIGN_DECELERATING
        shared_controls["STOP_SIGN_PREV_SPEED"] = lane_data.car_speed_data
        shared_controls["STOP_SIGN_HOLD_SECONDS"] = hold_seconds
        shared_controls["STOP_SIGN_IGNORE"] = True

    if custom_label != STOP_SIGN_LABEL and not shared_controls.get("STOP_SIGN_ACTIVE", False):
        shared_controls["STOP_SIGN_IGNORE"] = False

    stop_sign_forcing_stop = False
    if shared_controls.get("STOP_SIGN_ACTIVE", False):
        stop_sign_forcing_stop = _handle_stop_sign_state(
            shared_controls,
            lane_data,
            current_time=current_time,
        )

    should_stop = (
        obj_data.object_person_data == 1
        or shared_controls.get("EMERGENCY_STOP", 0) == 1
        or shared_controls.get("SAFE_STOP")
        or shared_controls.get("OBJ_SAFE_STOP")
        or obj_data.traffic_light_data == 0
    )

    if custom_label == DETOUR_LABEL:
        pass  # Placeholder for future detour handling
    elif custom_label == LOMBADA_LABEL:
        pass  # Placeholder for future bump/light handling

    if should_stop and not stop_sign_forcing_stop:
        _update_car_speed(shared_controls, lane_data, 0)


def handle_object_queue(manual_md, object_queue, obj_data: ObjectData):
    if manual_md:
        obj_data.custom_object_data = 0
        obj_data.custom_object_label = ""
        obj_data.object_person_data = 0
        obj_data.traffic_light_data = 2
        while not object_queue.empty():
            try:
                object_queue.get_nowait()
            except Empty:
                break
    else:
        try:
            new_obj = object_queue.get_nowait()
            obj_data.update(new_obj)
        except Empty:
            pass


def publish(lane_data: LaneData, obj_data: ObjectData, serial_comm, logger, verbose):
    payload = [
        lane_data.car_direction_data,
        lane_data.car_speed_data,
        obj_data.traffic_light_data,
    ]

    if not serial_comm.ensure_connection():
        return

    try:
        serial_comm.send(payload, verbose)
    except Exception as e:
        logger.error(f"Falha ao enviar dados: {e}")
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

