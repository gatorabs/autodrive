def map_direction(value, in_min=-32, in_max=32, out_min=0, out_max=180):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)