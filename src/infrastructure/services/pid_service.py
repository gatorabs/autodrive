from src.domain.models.pid.pid import PIDController
from src.domain.models.pid.pid_v2 import PIDV2Controller
from src.domain.constants.pid_constants import (
    KP,
    KD,
    KI,
    MIN_OUTPUT,
    MAX_OUTPUT,
    TARGET_CENTER_DISTANCE,
)

def pid_setup(use_new: bool, logger):
    cls = PIDV2Controller if use_new else PIDController
    return cls(set_point=TARGET_CENTER_DISTANCE,
               kp=KP, ki=KI, kd=KD,
               min_output=MIN_OUTPUT, max_output=MAX_OUTPUT,
               logger=logger)


def update_pid_from_controls(pid, controls,
                             default_set_point,
                             default_kp, default_ki, default_kd):

    pid.set_point = controls.get("Distance", default_set_point)
    pid.kp        = controls.get("KP",       default_kp)
    pid.ki        = controls.get("KI",       default_ki)
    pid.kd        = controls.get("KD",       default_kd)

def check_and_update_pid(pid, last_pid_flag, shared_controls, logger):
    current_pid_flag = shared_controls.get("NEW_PID")
    if current_pid_flag != last_pid_flag:
        pid = pid_setup(current_pid_flag, logger)
        logger.info(f"PID Controller atualizado para {'PID V2' if current_pid_flag else 'PID V1'}.")
        last_pid_flag = current_pid_flag
    return pid, last_pid_flag
