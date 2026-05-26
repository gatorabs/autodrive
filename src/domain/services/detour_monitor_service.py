"""Service responsible for detour sign tracking."""
from __future__ import annotations

from src.domain.services.detour_service import activate_detour_mode
from src.domain.constants.detour_constants import (
    DEVIATION_COUNTER_CONTROL,
    DETOUR_COUNT_KEY,
    DETOUR_IGNORE_KEY,
)

from .stop_sign_service import STOP_SIGN_LABEL

DETOUR_LABEL = "PLACA_DESVIO"


def handle_detour_detection(custom_label, shared_controls, tk_controls):
    if tk_controls is None or not hasattr(tk_controls, "get"):
        return

    if (
        shared_controls is None
        or not hasattr(shared_controls, "get")
        or not hasattr(shared_controls, "__setitem__")
    ):
        return

    if custom_label == STOP_SIGN_LABEL:
        activate_detour_mode(shared_controls, tk_controls)
        shared_controls[DETOUR_COUNT_KEY] = 0
        shared_controls[DETOUR_IGNORE_KEY] = False
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
        else:
            shared_controls[DETOUR_COUNT_KEY] = 0
            shared_controls[DETOUR_IGNORE_KEY] = False
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


__all__ = ["handle_detour_detection", "DETOUR_LABEL"]
