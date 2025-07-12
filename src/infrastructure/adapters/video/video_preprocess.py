import cv2 as cv
from src.application.services.lane_detection_service import get_warp_points_from_controls, bird_eye_full

def preprocess(frame, tk_controls, morph_kernel):
    canny_1   = tk_controls.get("F_Canny")
    canny_2   = tk_controls.get("S_Canny")
    side      = tk_controls.get("Side", 1)
    num_lines = tk_controls.get("Lines", 10)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (5, 5), 0)
    edges = cv.Canny(blur, canny_1, canny_2)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)

    warp_points = get_warp_points_from_controls(tk_controls)
    warped_roi  = bird_eye_full(edges, warp_points, draw_on=frame)

    return edges, warp_points, warped_roi, side, num_lines
