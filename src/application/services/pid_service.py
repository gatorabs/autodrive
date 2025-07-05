def update_pid_from_controls(pid, controls,
                             default_set_point,
                             default_kp, default_ki, default_kd):

    pid.set_point = controls.get("Distance", default_set_point)
    pid.kp        = controls.get("KP",       default_kp)
    pid.ki        = controls.get("KI",       default_ki)
    pid.kd        = controls.get("KD",       default_kd)

