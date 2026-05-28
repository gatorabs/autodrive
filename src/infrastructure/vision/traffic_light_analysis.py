import cv2
import numpy as np


def process_traffic_light_roi(roi):
    active_color = "Unknown"
    color_bgr = (255, 255, 255)
    traffic_light_state = 2

    if roi.size == 0:
        return active_color, color_bgr, traffic_light_state

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    height = gray.shape[0]
    third_height = height // 3

    if third_height == 0:
        return active_color, color_bgr, traffic_light_state

    red_roi = gray[0:third_height, :]
    yellow_roi = gray[third_height : 2 * third_height, :]
    green_roi = gray[2 * third_height : height, :]

    means = {
        "Red": np.nanmean(red_roi),
        "Yellow": np.nanmean(yellow_roi),
        "Green": np.nanmean(green_roi),
    }

    if any(np.isnan(value) for value in means.values()):
        return active_color, color_bgr, traffic_light_state

    active_color = max(means, key=means.get)

    if active_color == "Red":
        color_bgr = (0, 0, 255)
        traffic_light_state = 0
    elif active_color == "Yellow":
        color_bgr = (0, 255, 255)
        traffic_light_state = 1
    elif active_color == "Green":
        color_bgr = (0, 255, 0)
        traffic_light_state = 2

    return active_color, color_bgr, traffic_light_state
