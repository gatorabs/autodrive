import numpy as np
import cv2 as cv

from utils.real_time_trackbars import get_warp_points_trackbars


tl = (20, 0)
tr = (300, 0)
bl = (0, 20)
br = (320, 20)

def bird_eye(roi, calibrate):
    h, w = roi.shape

    if calibrate:
        tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = get_warp_points_trackbars()

        tl_cal = (tl_x, tl_y)
        tr_cal = (tr_x, tr_y)
        bl_cal = (bl_x, bl_y)
        br_cal = (br_x, br_y)

        return return_warped_roi(roi, tl_cal, tr_cal, bl_cal, br_cal, h, w)

    return return_warped_roi(roi, tl, tr, bl, br, h, w)

def return_warped_roi(roi, tl, tr, bl, br, h, w):
    cv.circle(roi, tl, 5, (255, 255, 255), 1)
    cv.circle(roi, tr, 5, (255, 255, 255), 1)
    cv.circle(roi, bl, 5, (255, 255, 255), 1)
    cv.circle(roi, br, 5, (255, 255, 255), 1)

    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([[0, 0], [0, 20], [330, 0], [330, 20]])

    M = cv.getPerspectiveTransform(pts1, pts2)
    warped_roi = cv.warpPerspective(roi, M, (w, h))

    return warped_roi
