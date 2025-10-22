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


def _update_car_speed(shared_controls, lane_data, speed):
    lane_data.car_speed_data = speed
    car_info = shared_controls.get("CAR_INFO", {})
    car_info["CAR_SPEED_DATA"] = speed
    shared_controls["CAR_INFO"] = car_info


def _resolve_custom_label(obj_data):
    if getattr(obj_data, "custom_object_label", ""):
        return obj_data.custom_object_label
    return CUSTOM_OBJECT_LABEL_BY_CODE.get(obj_data.custom_object_data, "")


def _get_stop_hold_seconds(tk_controls):
    tk_controls = tk_controls or {}
    try:
        hold_seconds = float(tk_controls.get("Timestamp", 5))
    except (TypeError, ValueError):
        hold_seconds = 5.0
    return max(0.0, hold_seconds)


def _get_stop_sign_deceleration_step(tk_controls):
    tk_controls = tk_controls or {}
    try:
        step = int(round(float(tk_controls.get("StopDecelerationStep", 10))))
    except (TypeError, ValueError):
        step = 10
    return max(1, step)


def _get_stop_sign_deceleration_interval(tk_controls):
    tk_controls = tk_controls or {}
    try:
        interval = float(tk_controls.get("StopDecelerationInterval", 0.2))
    except (TypeError, ValueError):
        interval = 0.2
    return max(0.0, interval)


def _record_stop_sign_requested_speed(shared_controls, lane_data, *, force=False):
    try:
        requested_speed = int(lane_data.car_speed_data)
    except (TypeError, ValueError):
        return

    requested_speed = max(0, min(255, requested_speed))

    if not force:
        decel_state = shared_controls.get("STOP_SIGN_DECEL_STATE")
        if decel_state:
            current_speed = max(0, int(decel_state.get("current_speed", 0)))
            if requested_speed == current_speed:
                return

    shared_controls["STOP_SIGN_PREV_SPEED"] = requested_speed


def _start_stop_sign_deceleration(shared_controls, initial_speed, tk_controls, current_time):
    step = _get_stop_sign_deceleration_step(tk_controls)
    interval = _get_stop_sign_deceleration_interval(tk_controls)
    try:
        starting_speed = int(initial_speed)
    except (TypeError, ValueError):
        starting_speed = 0
    shared_controls["STOP_SIGN_DECEL_STATE"] = {
        "current_speed": max(0, starting_speed),
        "step": step,
        "interval": interval,
        "last_update": current_time - interval,
    }


def _ensure_stop_sign_hold_timer(shared_controls, current_time):
    hold_seconds = shared_controls.get("STOP_SIGN_HOLD_SECONDS", 0.0)
    if hold_seconds > 0:
        resume_time = shared_controls.get("STOP_SIGN_RESUME_TIME")
        if resume_time is None or current_time > resume_time:
            shared_controls["STOP_SIGN_RESUME_TIME"] = current_time + hold_seconds
        shared_controls["STOP_SIGN_ACTIVE"] = True
    else:
        shared_controls["STOP_SIGN_ACTIVE"] = False
        shared_controls["STOP_SIGN_RESUME_TIME"] = current_time


def _apply_stop_sign_deceleration(shared_controls, tk_controls, current_time):
    state = shared_controls.get("STOP_SIGN_DECEL_STATE")
    if not state:
        return 0

    current_speed = max(0, int(state.get("current_speed", 0)))
    slider_step = _get_stop_sign_deceleration_step(tk_controls)
    step = state.get("step")
    if not isinstance(step, int) or step != slider_step:
        step = slider_step
        state["step"] = step

    slider_interval = _get_stop_sign_deceleration_interval(tk_controls)
    interval = state.get("interval")
    if not isinstance(interval, (int, float)) or interval != slider_interval:
        interval = slider_interval
        state["interval"] = interval

    if current_speed <= 0:
        state["current_speed"] = 0
        shared_controls["STOP_SIGN_DECEL_STATE"] = state
        _ensure_stop_sign_hold_timer(shared_controls, current_time)
        return 0

    last_update = state.get("last_update")
    if not isinstance(last_update, (int, float)):
        last_update = current_time - interval

    if interval > 0 and current_time - last_update < interval:
        state["last_update"] = last_update
        shared_controls["STOP_SIGN_DECEL_STATE"] = state
        return current_speed

    next_speed = max(current_speed - step, 0)
    state["current_speed"] = next_speed
    state["last_update"] = current_time
    shared_controls["STOP_SIGN_DECEL_STATE"] = state

    if next_speed == 0:
        _ensure_stop_sign_hold_timer(shared_controls, current_time)

    return next_speed


def _clear_stop_sign_state(shared_controls):
    shared_controls.pop("STOP_SIGN_DECEL_STATE", None)
    shared_controls.pop("STOP_SIGN_HOLD_SECONDS", None)
    shared_controls.pop("STOP_SIGN_RESUME_TIME", None)
    shared_controls.pop("STOP_SIGN_ACTIVE", None)


def publish_emergency_stop(obj_data, shared_controls, lane_data, tk_controls, *, now=None):
    current_time = time.monotonic() if now is None else now

    custom_label = _resolve_custom_label(obj_data)
    hold_seconds = _get_stop_hold_seconds(tk_controls) if custom_label == STOP_SIGN_LABEL else 0.0

    stop_sign_ignore = shared_controls.get("STOP_SIGN_IGNORE", False)
    stop_sign_active = shared_controls.get("STOP_SIGN_ACTIVE", False)
    stop_sign_hold = False

    if stop_sign_active:
        resume_time = shared_controls.get("STOP_SIGN_RESUME_TIME")
        if resume_time is not None and current_time >= resume_time:
            shared_controls["STOP_SIGN_ACTIVE"] = False
            shared_controls.pop("STOP_SIGN_RESUME_TIME", None)
            shared_controls.pop("STOP_SIGN_HOLD_SECONDS", None)
        else:
            stop_sign_hold = True
            _record_stop_sign_requested_speed(shared_controls, lane_data)

    if (
        not shared_controls.get("STOP_SIGN_ACTIVE", False)
        and custom_label == STOP_SIGN_LABEL
        and not stop_sign_ignore
    ):
        shared_controls["STOP_SIGN_ACTIVE"] = hold_seconds > 0
        shared_controls["STOP_SIGN_RESUME_TIME"] = None
        shared_controls["STOP_SIGN_HOLD_SECONDS"] = hold_seconds
        _record_stop_sign_requested_speed(shared_controls, lane_data, force=True)
        shared_controls["STOP_SIGN_IGNORE"] = True
        _start_stop_sign_deceleration(
            shared_controls, lane_data.car_speed_data, tk_controls, current_time
        )
        stop_sign_hold = True

    if custom_label != STOP_SIGN_LABEL and not shared_controls.get("STOP_SIGN_ACTIVE", False):
        shared_controls["STOP_SIGN_IGNORE"] = False

    decel_state = shared_controls.get("STOP_SIGN_DECEL_STATE")
    if decel_state:
        _record_stop_sign_requested_speed(shared_controls, lane_data)
        if decel_state.get("current_speed", 0) > 0:
            stop_sign_hold = True

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

    if stop_sign_hold:
        should_stop = True

    if should_stop:
        if stop_sign_hold and shared_controls.get("STOP_SIGN_DECEL_STATE"):
            target_speed = _apply_stop_sign_deceleration(shared_controls, tk_controls, current_time)
            _update_car_speed(shared_controls, lane_data, target_speed)
        else:
            _update_car_speed(shared_controls, lane_data, 0)
    else:
        prev_speed = shared_controls.pop("STOP_SIGN_PREV_SPEED", None)
        if prev_speed is not None and lane_data.car_speed_data == 0:
            _update_car_speed(shared_controls, lane_data, prev_speed)
        _clear_stop_sign_state(shared_controls)


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

