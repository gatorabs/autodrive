import math
_last_angle = 90

def map_direction(value, in_min=-32, in_max=32, out_min=0, out_max=180):
    global _last_angle
    if not math.isfinite(value):
        return _last_angle
    _last_angle = int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    return _last_angle

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def map_range(value, in_min, in_max, out_min, out_max, clamp_value=False):
    if in_min == in_max:
        raise ValueError("in_min e in_max não podem ser iguais")
    t = (value - in_min) / (in_max - in_min)
    if clamp_value:
        t = clamp(t, 0.0, 1.0)
    return int(round(out_min + t * (out_max - out_min)))