import time
from queue import Empty
from typing import Optional

from src.domain.models.lane_data.lane_data import LaneData
from src.domain.models.object_data.object_data import ObjectData
from src.infrastructure.services.object_detection_service import (
    CUSTOM_OBJECT_LABEL_BY_CODE,
)

from src.infrastructure.services.stop_sign_service import (
    STOP_SIGN_PREFIX,
    apply_deceleration as apply_stop_sign_deceleration,
    evaluate_stop_phase as evaluate_stop_sign_phase,
    handle_resume_phase as resume_from_stop_sign,
)
from src.infrastructure.services.bump_service import (
    BUMP_PREFIX,
    apply_deceleration as apply_bump_deceleration,
    evaluate_stop_phase as evaluate_bump_phase,
    handle_resume_phase as resume_from_bump,
)
from src.infrastructure.services.person_stop_service import (
    PERSON_PREFIX,
    handle_resume as resume_person_stop,
    prepare_stop as prepare_person_stop,
)
from src.infrastructure.services.traffic_light_service import (
    TRAFFIC_LIGHT_DECEL_STATE_KEY,
    TRAFFIC_LIGHT_LAST_SPEED_KEY,
    TRAFFIC_LIGHT_PREFIX,
    TRAFFIC_LIGHT_GREEN,
    apply_acceleration as apply_traffic_light_acceleration,
    apply_deceleration as apply_traffic_light_deceleration,
    evaluate_state as evaluate_traffic_light_state,
    prepare_acceleration as prepare_traffic_light_acceleration,
    start_deceleration as start_traffic_light_deceleration,
)
from src.infrastructure.services.detour_monitor_service import handle_detour_detection
from src.infrastructure.services import ramp_service
from src.infrastructure.utils import clamp_speed, prefixed

def publish_emergency_stop(
    obj_data,
    shared_controls,
    lane_data,
    tk_controls,
    *,
    now: Optional[float] = None,
):
    current_time = time.monotonic() if now is None else now

    custom_label = _resolve_custom_label(obj_data)

    traffic_light_value = getattr(obj_data, "traffic_light_data", TRAFFIC_LIGHT_GREEN)
    traffic_light_evaluation = evaluate_traffic_light_state(
        shared_controls, lane_data, traffic_light_value
    )

    stop_sign_phase = evaluate_stop_sign_phase(
        shared_controls, lane_data, tk_controls, custom_label, current_time
    )
    bump_phase = evaluate_bump_phase(
        shared_controls, lane_data, tk_controls, custom_label, current_time
    )

    person_detected = obj_data.object_person_data == 1
    prepare_person_stop(shared_controls, lane_data, person_detected)

    emergency_stop = (
        person_detected
        or shared_controls.get("EMERGENCY_STOP", 0) == 1
        or shared_controls.get("SAFE_STOP")
        or shared_controls.get("OBJ_SAFE_STOP")
    )

    should_stop = (
        emergency_stop
        or stop_sign_phase.hold_active
        or bump_phase.hold_active
        or traffic_light_evaluation.should_stop
    )

    handle_detour_detection(custom_label, shared_controls, tk_controls)

    updated_speed: Optional[int] = None

    if should_stop:
        for prefix in (STOP_SIGN_PREFIX, BUMP_PREFIX, PERSON_PREFIX, TRAFFIC_LIGHT_PREFIX):
            shared_controls.pop(prefixed(prefix, "ACCEL_STATE"), None)

        target_candidates = []

        if stop_sign_phase.has_deceleration:
            target_candidates.append(
                apply_stop_sign_deceleration(shared_controls, tk_controls, current_time)
            )
        if bump_phase.has_deceleration:
            target_candidates.append(
                apply_bump_deceleration(shared_controls, tk_controls, current_time)
            )
        if traffic_light_evaluation.should_stop:
            if not shared_controls.get(TRAFFIC_LIGHT_DECEL_STATE_KEY):
                current_speed = getattr(lane_data, "car_speed_data", 0)
                if current_speed > 0:
                    start_traffic_light_deceleration(
                        shared_controls,
                        current_speed,
                        tk_controls,
                        current_time,
                    )
            traffic_speed = apply_traffic_light_deceleration(
                shared_controls,
                tk_controls,
                current_time,
            )
            if traffic_speed is None:
                stop_speed = (
                    0
                    if traffic_light_evaluation.target_speed is None
                    else traffic_light_evaluation.target_speed
                )
                traffic_speed = clamp_speed(stop_speed)
            target_candidates.append(traffic_speed)

        if emergency_stop:
            target_speed = 0
        else:
            speeds = [speed for speed in target_candidates if speed is not None]
            target_speed = min(speeds) if speeds else 0

        _update_car_speed(shared_controls, lane_data, target_speed)
        updated_speed = target_speed
    else:
        shared_controls.pop(TRAFFIC_LIGHT_DECEL_STATE_KEY, None)

        stop_sign_speed = resume_from_stop_sign(
            shared_controls, lane_data, tk_controls, current_time
        )
        if stop_sign_speed is not None:
            _update_car_speed(shared_controls, lane_data, stop_sign_speed)
            updated_speed = stop_sign_speed

        bump_speed = resume_from_bump(
            shared_controls, lane_data, tk_controls, current_time
        )
        if bump_speed is not None:
            _update_car_speed(shared_controls, lane_data, bump_speed)
            updated_speed = bump_speed

        person_speed = resume_person_stop(
            shared_controls, lane_data, tk_controls, current_time, person_detected
        )
        if person_speed is not None:
            _update_car_speed(shared_controls, lane_data, person_speed)
            updated_speed = person_speed

        desired_traffic_speed: Optional[int] = None
        if traffic_light_evaluation.target_speed is not None:
            desired_traffic_speed = clamp_speed(traffic_light_evaluation.target_speed)
            if desired_traffic_speed <= 0:
                shared_controls.pop(prefixed(TRAFFIC_LIGHT_PREFIX, "ACCEL_STATE"), None)
                shared_controls.pop(prefixed(TRAFFIC_LIGHT_PREFIX, "PREV_SPEED"), None)
                if updated_speed is None or desired_traffic_speed != updated_speed:
                    _update_car_speed(shared_controls, lane_data, desired_traffic_speed)
                    updated_speed = desired_traffic_speed
            else:
                prepare_traffic_light_acceleration(
                    shared_controls,
                    lane_data,
                    tk_controls,
                    current_time,
                    desired_traffic_speed,
                )
        else:
            if not traffic_light_evaluation.should_stop:
                shared_controls.pop(prefixed(TRAFFIC_LIGHT_PREFIX, "PREV_SPEED"), None)

        traffic_light_speed = apply_traffic_light_acceleration(
            shared_controls,
            tk_controls,
            current_time,
        )
        if traffic_light_speed is not None:
            _update_car_speed(shared_controls, lane_data, traffic_light_speed)
            updated_speed = traffic_light_speed
        elif desired_traffic_speed is not None and desired_traffic_speed > 0:
            _update_car_speed(shared_controls, lane_data, desired_traffic_speed)
            updated_speed = desired_traffic_speed
            shared_controls.pop(prefixed(TRAFFIC_LIGHT_PREFIX, "PREV_SPEED"), None)
            ramp_service.clear_stop_state(shared_controls, prefix=TRAFFIC_LIGHT_PREFIX)

    return updated_speed

def handle_object_queue(manual_md, object_queue, obj_data: ObjectData):
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


# -----------------------
# Internals
# -----------------------

def _update_car_speed(shared_controls, lane_data, speed):
    speed = clamp_speed(speed)
    lane_data.car_speed_data = speed

    car_info = dict(shared_controls.get("CAR_INFO", {}))
    car_info["CAR_SPEED_DATA"] = speed
    shared_controls["CAR_INFO"] = car_info

    shared_controls["STOP_SIGN_LAST_SPEED"] = speed
    shared_controls["BUMP_LAST_SPEED"] = speed
    shared_controls["PERSON_LAST_SPEED"] = speed
    shared_controls[TRAFFIC_LIGHT_LAST_SPEED_KEY] = speed


def _resolve_custom_label(obj_data):
    label = getattr(obj_data, "custom_object_label", "") or ""
    if label:
        return label
    return CUSTOM_OBJECT_LABEL_BY_CODE.get(obj_data.custom_object_data, "")

__all__ = [
    "publish_emergency_stop",
    "handle_object_queue",
    "publish",
    "change_serial_port",
]
