from src.domain.models.pid.pid import PIDController
from src.domain.models.pid.pid_v2 import PIDV2Controller
from src.infrastructure.constants.usecases_constants.lane_process_constants import TARGET_CENTER_DISTANCE, KP, KI, KD, MIN_OUTPUT, MAX_OUTPUT

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

