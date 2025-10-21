import time
from queue import Empty

from src.domain.models.lane_data.lane_data import LaneData
from src.domain.models.object_data.object_data import ObjectData

STOP_SIGN_STATE_KEY = "STOP_SIGN_STATE"
_DEFAULT_STOP_STATE = {
    "active_until": 0.0,
    "awaiting_clear": False,
    "resumed": False,
    "restore_speed": None,
}


def _normalize_speed(value, fallback):
    if isinstance(value, (int, float)):
        return int(round(value))
    return int(round(fallback))


def publish_emergency_stop(obj_data, shared_controls, lane_data, tk_controls):
    now = time.monotonic()
    stop_state = shared_controls.get(STOP_SIGN_STATE_KEY)
    if not isinstance(stop_state, dict):
        stop_state = _DEFAULT_STOP_STATE.copy()
    else:
        stop_state = {
            "active_until": float(stop_state.get("active_until", 0.0)),
            "awaiting_clear": bool(stop_state.get("awaiting_clear", False)),
            "resumed": bool(stop_state.get("resumed", False)),
            "restore_speed": stop_state.get("restore_speed"),
        }

    shared_controls["DETOUR_SIGN_DETECTED"] = bool(obj_data.detour_sign_data)
    shared_controls["SPEED_BUMP_SIGN_DETECTED"] = bool(obj_data.speed_bump_sign_data)

    base_stop_conditions = (
        obj_data.object_person_data == 1
        or shared_controls.get("EMERGENCY_STOP", 0) == 1
        or shared_controls.get("SAFE_STOP")
        or shared_controls.get("OBJ_SAFE_STOP")
        or obj_data.traffic_light_data == 0
    )

    should_stop = base_stop_conditions

    try:
        stop_duration = float(tk_controls.get("Timestamp", 0))
    except (TypeError, ValueError):
        stop_duration = 0.0
    stop_duration = max(0.0, stop_duration)

    stop_sign_detected = obj_data.stop_sign_data == 1

    if stop_sign_detected:
        if not stop_state["awaiting_clear"]:
            desired_speed = shared_controls.get("CAR_SPEED_DATA", tk_controls.get("Speed", lane_data.car_speed_data))
            stop_state = {
                "active_until": now + stop_duration,
                "awaiting_clear": True,
                "resumed": stop_duration == 0.0,
                "restore_speed": desired_speed,
            }
        elif (not stop_state["resumed"]) and now >= stop_state["active_until"]:
            if not base_stop_conditions:
                restore_speed = stop_state.get("restore_speed", tk_controls.get("Speed", lane_data.car_speed_data))
                restore_speed = _normalize_speed(restore_speed, lane_data.car_speed_data)
                lane_data.car_speed_data = restore_speed
                car_info = shared_controls.get("CAR_INFO", {})
                car_info["CAR_SPEED_DATA"] = restore_speed
                shared_controls["CAR_INFO"] = car_info
                shared_controls["CAR_SPEED_DATA"] = restore_speed
            stop_state["resumed"] = True

        if (not stop_state["resumed"]) and now < stop_state["active_until"]:
            should_stop = True
        elif (not stop_state["resumed"]) and now >= stop_state["active_until"] and base_stop_conditions:
            should_stop = True

        shared_controls[STOP_SIGN_STATE_KEY] = stop_state
    else:
        if stop_state["awaiting_clear"]:
            shared_controls[STOP_SIGN_STATE_KEY] = _DEFAULT_STOP_STATE.copy()

    if should_stop:
        lane_data.car_speed_data = 0
        car_info = shared_controls.get("CAR_INFO", {})
        car_info["CAR_SPEED_DATA"] = 0
        shared_controls["CAR_INFO"] = car_info
        shared_controls["CAR_SPEED_DATA"] = 0

def handle_object_queue(manual_md, object_queue, obj_data: ObjectData):
    if manual_md:
        obj_data.custom_object_data = 0
        obj_data.object_person_data = 0
        obj_data.traffic_light_data = 2
        obj_data.stop_sign_data = 0
        obj_data.detour_sign_data = 0
        obj_data.speed_bump_sign_data = 0
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

