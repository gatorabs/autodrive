import time
from queue import Empty

from src.domain.models.lane_data.lane_data import LaneData
from src.domain.models.object_data.object_data import ObjectData
from src.infrastructure.services.object_detection_service import (
    CUSTOM_OBJECT_LABEL_BY_CODE,
)
from src.domain.constants.detour_constants import (
    DEVIATION_COUNTER_CONTROL,
    DETOUR_COUNT_KEY,
    DETOUR_IGNORE_KEY,
)
from src.infrastructure.services.detour_service import (
    activate_detour_mode,
    reset_detour_mode,
)

STOP_SIGN_LABEL = "PLACA_PARE"
DETOUR_LABEL = "PLACA_DESVIO"
LOMBADA_LABEL = "PLACA_LOMBADA"

def publish_emergency_stop(obj_data, shared_controls, lane_data, tk_controls, *, now=None):
    current_time = time.monotonic() if now is None else now

    custom_label = _resolve_custom_label(obj_data)
    stop_sign_ignore = shared_controls.get("STOP_SIGN_IGNORE", False)
    stop_sign_active = shared_controls.get("STOP_SIGN_ACTIVE", False)
    stop_sign_hold = False

    bump_ignore = shared_controls.get("BUMP_IGNORE", False)
    bump_active = shared_controls.get("BUMP_ACTIVE", False)
    bump_hold = False

    # --- STOP SIGN: checagem de expiração de hold já ativo
    if stop_sign_active:
        resume_time = shared_controls.get("STOP_SIGN_RESUME_TIME")
        if resume_time is not None and current_time >= resume_time:
            shared_controls["STOP_SIGN_ACTIVE"] = False
            shared_controls.pop("STOP_SIGN_RESUME_TIME", None)
            shared_controls.pop("STOP_SIGN_HOLD_SECONDS", None)
        else:
            stop_sign_hold = True
            _record_stop_sign_requested_speed(shared_controls, lane_data)

    # --- BUMP: checagem de expiração de hold já ativo
    if bump_active:
        resume_time = shared_controls.get("BUMP_RESUME_TIME")
        if resume_time is not None and current_time >= resume_time:
            shared_controls["BUMP_ACTIVE"] = False
            shared_controls.pop("BUMP_RESUME_TIME", None)
            shared_controls.pop("BUMP_HOLD_SECONDS", None)
        else:
            bump_hold = True
            _record_stop_sign_requested_speed(shared_controls, lane_data, prefix="BUMP")

    # --- Novo STOP SIGN detectado
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

    # --- Nova LOMBADA detectada
    if (
        not shared_controls.get("BUMP_ACTIVE", False)
        and custom_label == LOMBADA_LABEL
        and not bump_ignore
    ):
        reset_detour_mode(shared_controls, tk_controls)
        hold_seconds = _get_stop_hold_seconds(tk_controls)
        shared_controls["BUMP_ACTIVE"] = hold_seconds > 0
        shared_controls["BUMP_RESUME_TIME"] = None
        shared_controls["BUMP_HOLD_SECONDS"] = hold_seconds
        _record_stop_sign_requested_speed(shared_controls, lane_data, force=True, prefix="BUMP")

        shared_controls["BUMP_IGNORE"] = True

        starting_speed = _clamp_speed(lane_data.car_speed_data)
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

    # --- Reset de IGNORE quando não detectado
    if custom_label != STOP_SIGN_LABEL and not shared_controls.get("STOP_SIGN_ACTIVE", False):
        shared_controls["STOP_SIGN_IGNORE"] = False

    if custom_label != LOMBADA_LABEL and not shared_controls.get("BUMP_ACTIVE", False):
        shared_controls["BUMP_IGNORE"] = False

    # --- Estados de desaceleração em andamento mantêm hold
    decel_state = shared_controls.get("STOP_SIGN_DECEL_STATE")
    if decel_state:
        _record_stop_sign_requested_speed(shared_controls, lane_data)
        current_speed = _clamp_speed(decel_state.get("current_speed", 0))
        target_speed = _clamp_speed(decel_state.get("target_speed", 0))
        if current_speed > target_speed or shared_controls.get("STOP_SIGN_ACTIVE", False):
            stop_sign_hold = True

    bump_decel_state = shared_controls.get("BUMP_DECEL_STATE")
    if bump_decel_state:
        _record_stop_sign_requested_speed(shared_controls, lane_data, prefix="BUMP")
        current_speed = _clamp_speed(bump_decel_state.get("current_speed", 0))
        target_speed = _clamp_speed(bump_decel_state.get("target_speed", 0))
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

    should_stop = emergency_stop or stop_sign_hold or bump_hold

    _handle_detour_detection(custom_label, shared_controls, tk_controls)

    if should_stop:
        # Cancelar rampas de aceleração em curso
        shared_controls.pop("STOP_SIGN_ACCEL_STATE", None)
        shared_controls.pop("BUMP_ACCEL_STATE", None)
        shared_controls.pop("PERSON_ACCEL_STATE", None)

        # Preparar retomada após pessoa
        if person_detected:
            if shared_controls.get("PERSON_PREV_SPEED") is None:
                _record_stop_sign_requested_speed(shared_controls, lane_data, prefix="PERSON")
                prev_speed = shared_controls.get("PERSON_PREV_SPEED")
                if prev_speed in (None, 0):
                    fallback_speed = (
                        shared_controls.get("PERSON_LAST_SPEED")
                        or shared_controls.get("STOP_SIGN_LAST_SPEED")
                    )
                    inferred = _clamp_speed(fallback_speed)
                    if inferred > 0:
                        shared_controls["PERSON_PREV_SPEED"] = inferred
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

        speeds = [s for s in target_candidates if s is not None]
        target_speed = 0 if emergency_stop else (min(speeds) if speeds else 0)
        _update_car_speed(shared_controls, lane_data, target_speed)
    else:
        # --- STOP SIGN retomada
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
                fallback_speed = _clamp_speed(prev_speed)
                _update_car_speed(shared_controls, lane_data, fallback_speed)
                shared_controls.pop("STOP_SIGN_PREV_SPEED", None)
                _clear_stop_sign_state(shared_controls)
        else:
            _clear_stop_sign_state(shared_controls)

        # --- BUMP retomada
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
                fallback_speed = _clamp_speed(bump_prev_speed)
                _update_car_speed(shared_controls, lane_data, fallback_speed)
                shared_controls.pop("BUMP_PREV_SPEED", None)
                _clear_stop_sign_state(shared_controls, prefix="BUMP")
        else:
            _clear_stop_sign_state(shared_controls, prefix="BUMP")

        # --- PERSON retomada
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
                fallback_speed = _clamp_speed(person_prev_speed)
                _update_car_speed(shared_controls, lane_data, fallback_speed)
                shared_controls.pop("PERSON_PREV_SPEED", None)
                shared_controls["PERSON_STOP_ACTIVE"] = False
                _clear_stop_sign_state(shared_controls, prefix="PERSON")
        elif not person_detected:
            shared_controls.pop("PERSON_PREV_SPEED", None)
            shared_controls.pop("PERSON_STOP_ACTIVE", None)
            _clear_stop_sign_state(shared_controls, prefix="PERSON")


def _handle_detour_detection(custom_label, shared_controls, tk_controls):
    if tk_controls is None or not hasattr(tk_controls, "get"):
        return

    if (
        shared_controls is None
        or not hasattr(shared_controls, "get")
        or not hasattr(shared_controls, "__setitem__")
    ):
        return

    threshold = tk_controls.get(DEVIATION_COUNTER_CONTROL)
    try:
        threshold = int(round(float(threshold)))
    except (TypeError, ValueError):
        threshold = 0

    if threshold <= 0:
        if hasattr(shared_controls, "pop"):
            shared_controls.pop(DETOUR_COUNT_KEY, None)
            shared_controls.pop(DETOUR_IGNORE_KEY, None)
        return

    if custom_label == DETOUR_LABEL:
        if shared_controls.get(DETOUR_IGNORE_KEY):
            return

        count = int(shared_controls.get(DETOUR_COUNT_KEY, 0)) + 1
        shared_controls[DETOUR_COUNT_KEY] = count
        shared_controls[DETOUR_IGNORE_KEY] = True

        if count >= threshold:
            activate_detour_mode(shared_controls, tk_controls)
            shared_controls[DETOUR_COUNT_KEY] = 0
        return

    shared_controls[DETOUR_IGNORE_KEY] = False
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
        obj_data.traffic_light_data
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


# -----------------------
# Internos (estado/ramps)
# -----------------------

def _update_car_speed(shared_controls, lane_data, speed):
    speed = _clamp_speed(speed)
    lane_data.car_speed_data = speed

    car_info = dict(shared_controls.get("CAR_INFO", {}))
    car_info["CAR_SPEED_DATA"] = speed
    shared_controls["CAR_INFO"] = car_info

    # Telemetria (mantida): últimos outputs
    shared_controls["STOP_SIGN_LAST_SPEED"] = speed
    shared_controls["BUMP_LAST_SPEED"] = speed
    shared_controls["PERSON_LAST_SPEED"] = speed


def _resolve_custom_label(obj_data):
    label = getattr(obj_data, "custom_object_label", "") or ""
    if label:
        return label
    return CUSTOM_OBJECT_LABEL_BY_CODE.get(obj_data.custom_object_data, "")


def _get_stop_hold_seconds(tk_controls):
    tk_controls = tk_controls or {}
    raw = tk_controls.get("StopHoldSeconds", tk_controls.get("Timestamp", 5))
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 5.0


def _get_stop_sign_deceleration_step(tk_controls):
    tk_controls = tk_controls or {}
    try:
        step = int(round(float(tk_controls.get("StopDecelerationStep", 10))))
    except (TypeError, ValueError):
        step = 10
    return max(1, step)


def _get_stop_sign_ramp_interval(tk_controls):
    """
    Lê intervalo sem mutar tk_controls; suporta chaves legadas.
    """
    tk_controls = tk_controls or {}
    raw_value = tk_controls.get("StopRampInterval")

    if raw_value is None:
        for legacy_key in ("StopDecelerationInterval", "StopAccelerationInterval"):
            if legacy_key in tk_controls:
                raw_value = tk_controls[legacy_key]
                break

    if raw_value is None:
        raw_value = 0.2

    try:
        interval = float(raw_value)
    except (TypeError, ValueError):
        interval = 0.2

    return max(0.0, interval)


def _record_stop_sign_requested_speed(shared_controls, lane_data, *, force=False, prefix="STOP_SIGN"):
    requested_speed = _clamp_speed(lane_data.car_speed_data)

    if not force:
        decel_state = shared_controls.get(_prefixed(prefix, "DECEL_STATE"))
        if decel_state:
            current_speed = _clamp_speed(decel_state.get("current_speed", 0))
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

    starting_speed = _clamp_speed(initial_speed)
    desired_target = _clamp_speed(target_speed)
    desired_target = max(0, min(starting_speed, desired_target))

    shared_controls[_prefixed(prefix, "DECEL_STATE")] = {
        "current_speed": starting_speed,
        "target_speed": desired_target,
        "step": step,
        "interval": interval,
        "last_update": current_time - interval,  # aplica primeiro passo imediatamente
    }


def _ensure_stop_sign_hold_timer(shared_controls, current_time, prefix="STOP_SIGN"):
    key_hold = _prefixed(prefix, "HOLD_SECONDS")
    key_resume = _prefixed(prefix, "RESUME_TIME")
    key_active = _prefixed(prefix, "ACTIVE")

    hold_seconds = float(shared_controls.get(key_hold, 0.0) or 0.0)
    resume_time = shared_controls.get(key_resume)

    if hold_seconds <= 0.0:
        shared_controls[key_active] = False
        shared_controls[key_resume] = current_time  # já pode retomar
        return

    if resume_time is None:
        shared_controls[key_resume] = current_time + hold_seconds
        shared_controls[key_active] = True
        return

    # Já havia prazo: não renovar. Apenas atualizar flag.
    shared_controls[key_active] = current_time < resume_time


def _apply_stop_sign_deceleration(shared_controls, tk_controls, current_time, *, prefix="STOP_SIGN"):
    state = shared_controls.get(_prefixed(prefix, "DECEL_STATE"))
    if not state:
        return 0

    current_speed = _clamp_speed(state.get("current_speed", 0))
    target_speed = _clamp_speed(state.get("target_speed", 0))

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

    desired_speed = _clamp_speed(target_speed)

    last_output = shared_controls.get(_prefixed(prefix, "LAST_SPEED"))
    if last_output is None:
        last_output = current_speed

    starting_speed = _clamp_speed(last_output)
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


def _apply_stop_sign_acceleration(shared_controls, tk_controls, current_time, *, prefix="STOP_SIGN"):
    state = shared_controls.get(_prefixed(prefix, "ACCEL_STATE"))
    if not state:
        return None

    target_speed = _clamp_speed(state.get("target_speed", 0))

    latest_target = shared_controls.get(_prefixed(prefix, "PREV_SPEED"))
    if latest_target is not None:
        latest_target_int = _clamp_speed(latest_target)
        if latest_target_int != target_speed:
            target_speed = latest_target_int
            state["target_speed"] = target_speed

    current_speed = _clamp_speed(state.get("current_speed", 0))

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

# -----------------------
# Helpers utilitários
# -----------------------

def _prefixed(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}"


def _safe_int(x, default=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return default


def _clamp_speed(x, lo=0, hi=255):
    return max(lo, min(hi, _safe_int(x, lo)))
