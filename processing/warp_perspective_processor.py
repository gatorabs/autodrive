import numpy as np
import cv2 as cv

from utils.real_time_trackbars import get_warp_points_trackbars
from utils.constants import tl,tr,bl,br

def bird_eye(roi, calibrate, frame=None):
    h, w = roi.shape

    if calibrate:
        tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = get_warp_points_trackbars()

        tl_cal = (tl_x, tl_y)
        tr_cal = (tr_x, tr_y)
        bl_cal = (bl_x, bl_y)
        br_cal = (br_x, br_y)

        cv.circle(roi, tl_cal, 1, (255, 0, 255), 3)
        cv.circle(roi, tr_cal, 1, (255, 0, 255), 3)
        cv.circle(roi, bl_cal, 1, (255, 0, 255), 3)
        cv.circle(roi, br_cal, 1, (255, 0, 255), 3)

        return return_warped_roi(roi, tl_cal, tr_cal, bl_cal, br_cal, h, w)

    return return_warped_roi(roi, tl, tr, bl, br, h, w)

def return_warped_roi(roi, tl, tr, bl, br, h, w):
    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([[0, 0], [0, h], [w, 0], [w, h]])

    M = cv.getPerspectiveTransform(pts1, pts2)
    warped_roi = cv.warpPerspective(roi, M, (w, h))

    return warped_roi

