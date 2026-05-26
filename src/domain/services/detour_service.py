from typing import Any

from src.domain.constants.detour_constants import (
    DETOUR_ACTIVE_KEY,
    DETOUR_COUNT_KEY,
    DETOUR_DISTANCE_OFFSET,
    DETOUR_IGNORE_KEY,
    DETOUR_PREV_SETTINGS_KEY,
    DETOUR_TARGET_BR_X,
    DETOUR_TARGET_TR_X,
    DETOUR_FORCED_SIDE,
)


def activate_detour_mode(shared_controls: Any, tk_controls: Any) -> None:
    if not _controls_are_mutable(shared_controls, tk_controls):
        return

    if shared_controls.get(DETOUR_ACTIVE_KEY):
        return

    previous_values = shared_controls.get(DETOUR_PREV_SETTINGS_KEY)
    if not isinstance(previous_values, dict):
        previous_values = {
            "Distance": tk_controls.get("Distance") if hasattr(tk_controls, "get") else None,
            "tr_x": tk_controls.get("tr_x") if hasattr(tk_controls, "get") else None,
            "br_x": tk_controls.get("br_x") if hasattr(tk_controls, "get") else None,
        }
        shared_controls[DETOUR_PREV_SETTINGS_KEY] = previous_values

    current_distance = tk_controls.get("Distance") if hasattr(tk_controls, "get") else None
    forced_distance = _calculate_forced_distance(current_distance)

    _set_control_value(tk_controls, "Side", DETOUR_FORCED_SIDE)
    _set_control_value(tk_controls, "Distance", forced_distance)
    _set_control_value(tk_controls, "tr_x", DETOUR_TARGET_TR_X)
    _set_control_value(tk_controls, "br_x", DETOUR_TARGET_BR_X)

    shared_controls[DETOUR_ACTIVE_KEY] = True


def reset_detour_mode(shared_controls: Any, tk_controls: Any) -> None:
    if not _controls_are_mutable(shared_controls, tk_controls):
        return

    if not shared_controls.get(DETOUR_ACTIVE_KEY):
        return

    previous_values = None
    if hasattr(shared_controls, "pop"):
        previous_values = shared_controls.pop(DETOUR_PREV_SETTINGS_KEY, None)
    else:
        previous_values = shared_controls.get(DETOUR_PREV_SETTINGS_KEY)
        if hasattr(shared_controls, "__delitem__"):
            try:
                del shared_controls[DETOUR_PREV_SETTINGS_KEY]
            except KeyError:
                pass

    if isinstance(previous_values, dict):
        for key in ("Distance", "tr_x", "br_x"):
            value = previous_values.get(key)
            if value is not None:
                tk_controls[key] = value

    shared_controls[DETOUR_ACTIVE_KEY] = False
    if hasattr(shared_controls, "pop"):
        shared_controls.pop(DETOUR_COUNT_KEY, None)
    shared_controls[DETOUR_IGNORE_KEY] = False


def _controls_are_mutable(shared_controls: Any, tk_controls: Any) -> bool:
    return all(
        [
            shared_controls is not None,
            tk_controls is not None,
            hasattr(shared_controls, "get"),
            hasattr(shared_controls, "__setitem__"),
            hasattr(tk_controls, "__setitem__"),
        ]
    )


def _set_control_value(tk_controls: Any, key: str, value: Any) -> None:
    if value is None:
        return
    if tk_controls is None or not hasattr(tk_controls, "__setitem__"):
        return
    current = tk_controls.get(key) if hasattr(tk_controls, "get") else None
    if current == value:
        return
    tk_controls[key] = value


def _calculate_forced_distance(current_distance: Any) -> Any:
    if isinstance(current_distance, (int, float)):
        return current_distance - DETOUR_DISTANCE_OFFSET

    if isinstance(current_distance, str):
        try:
            numeric_value = float(current_distance)
        except ValueError:
            return None
        forced_distance = numeric_value - DETOUR_DISTANCE_OFFSET
        # Preserve integer-looking strings as ints when possible
        if forced_distance.is_integer():
            return int(forced_distance)
        return forced_distance

    return None
