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


def _prefixed(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}"


def publish_emergency_stop(obj_data, shared_controls, lane_data, tk_controls, *, now=None):
    current_time = time.monotonic() if now is None else now

    custom_label = _resolve_custom_label(obj_data)
    stop_sign_ignore = shared_controls.get("STOP_SIGN_IGNORE", False)
    stop_sign_active = shared_controls.get("STOP_SIGN_ACTIVE", False)
    stop_sign_hold = False

    bump_ignore = shared_controls.get("BUMP_IGNORE", False)
    bump_active = shared_controls.get("BUMP_ACTIVE", False)
    bump_hold = False

    if stop_sign_active:
        resume_time = shared_controls.get("STOP_SIGN_RESUME_TIME")
        if resume_time is not None and current_time >= resume_time:
            shared_controls["STOP_SIGN_ACTIVE"] = False
            shared_controls.pop("STOP_SIGN_RESUME_TIME", None)
            shared_controls.pop("STOP_SIGN_HOLD_SECONDS", None)
        else:
            stop_sign_hold = True
            _record_stop_sign_requested_speed(shared_controls, lane_data)

    if bump_active:
        resume_time = shared_controls.get("BUMP_RESUME_TIME")
        if resume_time is not None and current_time >= resume_time:
            shared_controls["BUMP_ACTIVE"] = False
            shared_controls.pop("BUMP_RESUME_TIME", None)
            shared_controls.pop("BUMP_HOLD_SECONDS", None)
        else:
            bump_hold = True
            _record_stop_sign_requested_speed(shared_controls, lane_data, prefix="BUMP")

    if (
        not shared_controls.get("STOP_SIGN_ACTIVE", False)
        and custom_label == STOP_SIGN_LABEL
        and not stop_sign_ignore
    ):
        hold_seconds = _get_stop_hold_seconds(tk_controls)
        shared_controls["STOP_SIGN_ACTIVE"] = hold_seconds > 0
        shared_controls["STOP_SIGN_RESUME_TIME"] = None
        shared_controls["STOP_SIGN_HOLD_SECONDS"] = hold_seconds
        _record_stop_sign_requested_speed(shared_controls, lane_data, force=True)
        shared_controls["STOP_SIGN_IGNORE"] = True
        _start_stop_sign_deceleration(
            shared_controls, lane_data.car_speed_data, tk_controls, current_time
        )
        stop_sign_hold = True

    if (
        not shared_controls.get("BUMP_ACTIVE", False)
        and custom_label == LOMBADA_LABEL
        and not bump_ignore
    ):
        hold_seconds = _get_stop_hold_seconds(tk_controls)
        shared_controls["BUMP_ACTIVE"] = hold_seconds > 0
        shared_controls["BUMP_RESUME_TIME"] = None
        shared_controls["BUMP_HOLD_SECONDS"] = hold_seconds
        _record_stop_sign_requested_speed(shared_controls, lane_data, force=True, prefix="BUMP")
        shared_controls["BUMP_IGNORE"] = True
        try:
            starting_speed = int(lane_data.car_speed_data)
        except (TypeError, ValueError):
            starting_speed = 0
        starting_speed = max(0, starting_speed)
        target_speed = max(0, starting_speed // 2)
        _start_stop_sign_deceleration(
            shared_controls,
            lane_data.car_speed_data,
            tk_controls,
            current_time,
            prefix="BUMP",
            target_speed=target_speed,
        )
        bump_hold = True

    if custom_label != STOP_SIGN_LABEL and not shared_controls.get("STOP_SIGN_ACTIVE", False):
        shared_controls["STOP_SIGN_IGNORE"] = False

    if custom_label != LOMBADA_LABEL and not shared_controls.get("BUMP_ACTIVE", False):
        shared_controls["BUMP_IGNORE"] = False

    decel_state = shared_controls.get("STOP_SIGN_DECEL_STATE")
    if decel_state:
        _record_stop_sign_requested_speed(shared_controls, lane_data)
        try:
            current_speed = int(decel_state.get("current_speed", 0))
        except (TypeError, ValueError):
            current_speed = 0
        try:
            target_speed = int(decel_state.get("target_speed", 0))
        except (TypeError, ValueError):
            target_speed = 0
        current_speed = max(0, current_speed)
        target_speed = max(0, target_speed)
        if current_speed > target_speed or shared_controls.get("STOP_SIGN_ACTIVE", False):
            stop_sign_hold = True

    bump_decel_state = shared_controls.get("BUMP_DECEL_STATE")
    if bump_decel_state:
        _record_stop_sign_requested_speed(shared_controls, lane_data, prefix="BUMP")
        try:
            current_speed = int(bump_decel_state.get("current_speed", 0))
        except (TypeError, ValueError):
            current_speed = 0
        try:
            target_speed = int(bump_decel_state.get("target_speed", 0))
        except (TypeError, ValueError):
            target_speed = 0
        current_speed = max(0, current_speed)
        target_speed = max(0, target_speed)
        if current_speed > target_speed or shared_controls.get("BUMP_ACTIVE", False):
            bump_hold = True

    person_detected = obj_data.object_person_data == 1

    emergency_stop = (
        person_detected
        or shared_controls.get("EMERGENCY_STOP", 0) == 1
        or shared_controls.get("SAFE_STOP")
        or shared_controls.get("OBJ_SAFE_STOP")
        or obj_data.traffic_light_data == 0
    )

    should_stop = emergency_stop

    if custom_label == DETOUR_LABEL:
        pass  # Placeholder for future detour handling

    if stop_sign_hold or bump_hold:
        should_stop = True

    if should_stop:
        shared_controls.pop("STOP_SIGN_ACCEL_STATE", None)
        shared_controls.pop("BUMP_ACCEL_STATE", None)
        shared_controls.pop("PERSON_ACCEL_STATE", None)

        if person_detected:
            if shared_controls.get("PERSON_PREV_SPEED") is None:
                _record_stop_sign_requested_speed(
                    shared_controls, lane_data, prefix="PERSON"
                )
                prev_speed = shared_controls.get("PERSON_PREV_SPEED")
                if prev_speed in (None, 0):
                    fallback_speed = shared_controls.get("PERSON_LAST_SPEED")
                    if fallback_speed is None:
                        fallback_speed = shared_controls.get("STOP_SIGN_LAST_SPEED")
                    try:
                        inferred_speed = int(fallback_speed)
                    except (TypeError, ValueError):
                        inferred_speed = 0
                    inferred_speed = max(0, min(255, inferred_speed))
                    if inferred_speed > 0:
                        shared_controls["PERSON_PREV_SPEED"] = inferred_speed
            shared_controls["PERSON_STOP_ACTIVE"] = True

        target_candidates = []
        if stop_sign_hold and shared_controls.get("STOP_SIGN_DECEL_STATE"):
            target_candidates.append(
                _apply_stop_sign_deceleration(shared_controls, tk_controls, current_time)
            )
        if bump_hold and shared_controls.get("BUMP_DECEL_STATE"):
            target_candidates.append(
                _apply_stop_sign_deceleration(
                    shared_controls, tk_controls, current_time, prefix="BUMP"
                )
            )

        speeds = [speed for speed in target_candidates if speed is not None]
        if emergency_stop:
            target_speed = 0
        else:
            target_speed = min(speeds) if speeds else 0
        _update_car_speed(shared_controls, lane_data, target_speed)
    else:
        shared_controls.pop("STOP_SIGN_DECEL_STATE", None)
        prev_speed = shared_controls.get("STOP_SIGN_PREV_SPEED")
        if prev_speed is not None:
            accel_state = shared_controls.get("STOP_SIGN_ACCEL_STATE")
            if not accel_state:
                _start_stop_sign_acceleration(
                    shared_controls,
                    lane_data.car_speed_data,
                    prev_speed,
                    tk_controls,
                    current_time,
                )

            result = _apply_stop_sign_acceleration(shared_controls, tk_controls, current_time)
            if result is not None:
                speed, finished = result
                _update_car_speed(shared_controls, lane_data, speed)
                if finished:
                    shared_controls.pop("STOP_SIGN_PREV_SPEED", None)
                    _clear_stop_sign_state(shared_controls)
            else:
                try:
                    fallback_speed = int(prev_speed)
                except (TypeError, ValueError):
                    fallback_speed = 0
                fallback_speed = max(0, fallback_speed)
                _update_car_speed(shared_controls, lane_data, fallback_speed)
                shared_controls.pop("STOP_SIGN_PREV_SPEED", None)
                _clear_stop_sign_state(shared_controls)
        else:
            _clear_stop_sign_state(shared_controls)

        shared_controls.pop("BUMP_DECEL_STATE", None)
        bump_prev_speed = shared_controls.get("BUMP_PREV_SPEED")
        if bump_prev_speed is not None:
            bump_accel_state = shared_controls.get("BUMP_ACCEL_STATE")
            if not bump_accel_state:
                _start_stop_sign_acceleration(
                    shared_controls,
                    lane_data.car_speed_data,
                    bump_prev_speed,
                    tk_controls,
                    current_time,
                    prefix="BUMP",
                )

            result = _apply_stop_sign_acceleration(
                shared_controls, tk_controls, current_time, prefix="BUMP"
            )
            if result is not None:
                speed, finished = result
                _update_car_speed(shared_controls, lane_data, speed)
                if finished:
                    shared_controls.pop("BUMP_PREV_SPEED", None)
                    _clear_stop_sign_state(shared_controls, prefix="BUMP")
            else:
                try:
                    fallback_speed = int(bump_prev_speed)
                except (TypeError, ValueError):
                    fallback_speed = 0
                fallback_speed = max(0, fallback_speed)
                _update_car_speed(shared_controls, lane_data, fallback_speed)
                shared_controls.pop("BUMP_PREV_SPEED", None)
                _clear_stop_sign_state(shared_controls, prefix="BUMP")
        else:
            _clear_stop_sign_state(shared_controls, prefix="BUMP")

        person_prev_speed = shared_controls.get("PERSON_PREV_SPEED")
        if (
            person_prev_speed is not None
            and shared_controls.get("PERSON_STOP_ACTIVE", False)
            and not person_detected
        ):
            person_accel_state = shared_controls.get("PERSON_ACCEL_STATE")
            if not person_accel_state:
                _start_stop_sign_acceleration(
                    shared_controls,
                    lane_data.car_speed_data,
                    person_prev_speed,
                    tk_controls,
                    current_time,
                    prefix="PERSON",
                )

            result = _apply_stop_sign_acceleration(
                shared_controls, tk_controls, current_time, prefix="PERSON"
            )
            if result is not None:
                speed, finished = result
                _update_car_speed(shared_controls, lane_data, speed)
                if finished:
                    shared_controls.pop("PERSON_PREV_SPEED", None)
                    shared_controls["PERSON_STOP_ACTIVE"] = False
                    _clear_stop_sign_state(shared_controls, prefix="PERSON")
            else:
                try:
                    fallback_speed = int(person_prev_speed)
                except (TypeError, ValueError):
                    fallback_speed = 0
                fallback_speed = max(0, fallback_speed)
                _update_car_speed(shared_controls, lane_data, fallback_speed)
                shared_controls.pop("PERSON_PREV_SPEED", None)
                shared_controls["PERSON_STOP_ACTIVE"] = False
                _clear_stop_sign_state(shared_controls, prefix="PERSON")
        elif not person_detected:
            shared_controls.pop("PERSON_PREV_SPEED", None)
            shared_controls.pop("PERSON_STOP_ACTIVE", None)
            _clear_stop_sign_state(shared_controls, prefix="PERSON")


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

def _update_car_speed(shared_controls, lane_data, speed):
    lane_data.car_speed_data = speed
    car_info = shared_controls.get("CAR_INFO", {})
    car_info["CAR_SPEED_DATA"] = speed
    shared_controls["CAR_INFO"] = car_info
    shared_controls["STOP_SIGN_LAST_SPEED"] = speed
    shared_controls["BUMP_LAST_SPEED"] = speed
    shared_controls["PERSON_LAST_SPEED"] = speed


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


def _get_stop_sign_ramp_interval(tk_controls):
    tk_controls = tk_controls or {}

    raw_value = None
    if "StopRampInterval" in tk_controls:
        raw_value = tk_controls.get("StopRampInterval")
    else:
        for legacy_key in ("StopDecelerationInterval", "StopAccelerationInterval"):
            if legacy_key in tk_controls:
                raw_value = tk_controls.get(legacy_key)
                break

    if raw_value is None:
        raw_value = 0.2

    try:
        interval = float(raw_value)
    except (TypeError, ValueError):
        interval = 0.2

    interval = max(0.0, interval)

    if tk_controls.get("StopRampInterval") != interval:
        tk_controls["StopRampInterval"] = interval

    return interval


def _record_stop_sign_requested_speed(shared_controls, lane_data, *, force=False, prefix="STOP_SIGN"):
    try:
        requested_speed = int(lane_data.car_speed_data)
    except (TypeError, ValueError):
        return

    requested_speed = max(0, min(255, requested_speed))

    if not force:
        decel_state = shared_controls.get(_prefixed(prefix, "DECEL_STATE"))
        if decel_state:
            current_speed = max(0, int(decel_state.get("current_speed", 0)))
            if requested_speed == current_speed:
                return

    shared_controls[_prefixed(prefix, "PREV_SPEED")] = requested_speed


def _start_stop_sign_deceleration(
    shared_controls,
    initial_speed,
    tk_controls,
    current_time,
    *,
    prefix="STOP_SIGN",
    target_speed=0,
):
    step = _get_stop_sign_deceleration_step(tk_controls)
    interval = _get_stop_sign_ramp_interval(tk_controls)
    try:
        starting_speed = int(initial_speed)
    except (TypeError, ValueError):
        starting_speed = 0
    starting_speed = max(0, starting_speed)
    try:
        desired_target = int(target_speed)
    except (TypeError, ValueError):
        desired_target = 0
    desired_target = max(0, min(starting_speed, desired_target))

    shared_controls[_prefixed(prefix, "DECEL_STATE")] = {
        "current_speed": starting_speed,
        "target_speed": desired_target,
        "step": step,
        "interval": interval,
        "last_update": current_time - interval,
    }


def _ensure_stop_sign_hold_timer(shared_controls, current_time, prefix="STOP_SIGN"):
    hold_seconds = shared_controls.get(_prefixed(prefix, "HOLD_SECONDS"), 0.0)
    if hold_seconds > 0:
        resume_time = shared_controls.get(_prefixed(prefix, "RESUME_TIME"))
        if resume_time is None or current_time > resume_time:
            shared_controls[_prefixed(prefix, "RESUME_TIME")] = current_time + hold_seconds
        shared_controls[_prefixed(prefix, "ACTIVE")] = True
    else:
        shared_controls[_prefixed(prefix, "ACTIVE")] = False
        shared_controls[_prefixed(prefix, "RESUME_TIME")] = current_time


def _apply_stop_sign_deceleration(
    shared_controls, tk_controls, current_time, *, prefix="STOP_SIGN"
):
    state = shared_controls.get(_prefixed(prefix, "DECEL_STATE"))
    if not state:
        return 0

    current_speed = max(0, int(state.get("current_speed", 0)))
    try:
        target_speed = int(state.get("target_speed", 0))
    except (TypeError, ValueError):
        target_speed = 0
    target_speed = max(0, target_speed)

    slider_step = _get_stop_sign_deceleration_step(tk_controls)
    step = state.get("step")
    if not isinstance(step, int) or step != slider_step:
        step = slider_step
        state["step"] = step

    slider_interval = _get_stop_sign_ramp_interval(tk_controls)
    interval = state.get("interval")
    if not isinstance(interval, (int, float)) or interval != slider_interval:
        interval = slider_interval
        state["interval"] = interval

    if current_speed <= target_speed:
        state["current_speed"] = target_speed
        shared_controls[_prefixed(prefix, "DECEL_STATE")] = state
        _ensure_stop_sign_hold_timer(shared_controls, current_time, prefix=prefix)
        return target_speed

    last_update = state.get("last_update")
    if not isinstance(last_update, (int, float)):
        last_update = current_time - interval

    if interval > 0 and current_time - last_update < interval:
        state["last_update"] = last_update
        shared_controls[_prefixed(prefix, "DECEL_STATE")] = state
        return current_speed

    next_speed = max(current_speed - step, target_speed)
    state["current_speed"] = next_speed
    state["last_update"] = current_time
    shared_controls[_prefixed(prefix, "DECEL_STATE")] = state

    if next_speed <= target_speed:
        state["current_speed"] = target_speed
        shared_controls[_prefixed(prefix, "DECEL_STATE")] = state
        _ensure_stop_sign_hold_timer(shared_controls, current_time, prefix=prefix)
        return target_speed

    return next_speed


def _start_stop_sign_acceleration(
    shared_controls,
    current_speed,
    target_speed,
    tk_controls,
    current_time,
    *,
    prefix="STOP_SIGN",
):
    step = _get_stop_sign_deceleration_step(tk_controls)
    interval = _get_stop_sign_ramp_interval(tk_controls)

    try:
        desired_speed = int(target_speed)
    except (TypeError, ValueError):
        desired_speed = 0

    desired_speed = max(0, min(255, desired_speed))

    last_output = shared_controls.get(_prefixed(prefix, "LAST_SPEED"))
    if last_output is None:
        last_output = current_speed

    try:
        starting_speed = int(last_output)
    except (TypeError, ValueError):
        try:
            starting_speed = int(current_speed)
        except (TypeError, ValueError):
            starting_speed = 0

    starting_speed = max(0, min(desired_speed, starting_speed))

    if desired_speed <= 0:
        shared_controls.pop(_prefixed(prefix, "ACCEL_STATE"), None)
        return

    shared_controls[_prefixed(prefix, "ACCEL_STATE")] = {
        "current_speed": starting_speed,
        "target_speed": desired_speed,
        "step": step,
        "interval": interval,
        "last_update": current_time - interval,
    }


def _apply_stop_sign_acceleration(
    shared_controls, tk_controls, current_time, *, prefix="STOP_SIGN"
):
    state = shared_controls.get(_prefixed(prefix, "ACCEL_STATE"))
    if not state:
        return None

    try:
        target_speed = int(state.get("target_speed", 0))
    except (TypeError, ValueError):
        target_speed = 0

    latest_target = shared_controls.get(_prefixed(prefix, "PREV_SPEED"))
    if latest_target is not None:
        try:
            latest_target_int = int(latest_target)
        except (TypeError, ValueError):
            latest_target_int = target_speed
        latest_target_int = max(0, min(255, latest_target_int))
        if latest_target_int != target_speed:
            target_speed = latest_target_int
            state["target_speed"] = target_speed

    target_speed = max(0, target_speed)

    try:
        current_speed = int(state.get("current_speed", 0))
    except (TypeError, ValueError):
        current_speed = 0

    current_speed = max(0, current_speed)

    slider_step = _get_stop_sign_deceleration_step(tk_controls)
    step = state.get("step")
    if not isinstance(step, int) or step != slider_step:
        step = slider_step
        state["step"] = step

    slider_interval = _get_stop_sign_ramp_interval(tk_controls)
    interval = state.get("interval")
    if not isinstance(interval, (int, float)) or interval != slider_interval:
        interval = slider_interval
        state["interval"] = interval

    if target_speed <= 0 or current_speed >= target_speed:
        shared_controls.pop(_prefixed(prefix, "ACCEL_STATE"), None)
        return target_speed, True

    last_update = state.get("last_update")
    if not isinstance(last_update, (int, float)):
        last_update = current_time - interval

    if interval > 0 and current_time - last_update < interval:
        state["last_update"] = last_update
        shared_controls[_prefixed(prefix, "ACCEL_STATE")] = state
        return current_speed, False

    next_speed = min(current_speed + step, target_speed)
    state["current_speed"] = next_speed
    state["last_update"] = current_time

    if next_speed >= target_speed:
        shared_controls.pop(_prefixed(prefix, "ACCEL_STATE"), None)
        return target_speed, True

    shared_controls[_prefixed(prefix, "ACCEL_STATE")] = state
    return next_speed, False


def _clear_stop_sign_state(shared_controls, prefix="STOP_SIGN"):
    shared_controls.pop(_prefixed(prefix, "DECEL_STATE"), None)
    shared_controls.pop(_prefixed(prefix, "HOLD_SECONDS"), None)
    shared_controls.pop(_prefixed(prefix, "RESUME_TIME"), None)
    shared_controls.pop(_prefixed(prefix, "ACTIVE"), None)
    shared_controls.pop(_prefixed(prefix, "ACCEL_STATE"), None)
