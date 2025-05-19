import numpy as np
import cv2 as cv

from utils.real_time_trackbars import get_warp_points_trackbars


def bird_eye(roi):
    h, w = roi.shape[:2]

    src_points = np.float32([
        [0, 0],
        [w, 0],
        [0, h],
        [w, h]
    ])

    dst_points = np.float32([
        [0, 0],
        [w, 0],
        [w * 0.2, h],  # 20% do lado esquerdo
        [w * 0.8, h]   # 80% do lado direito
    ])

    M = cv.getPerspectiveTransform(src_points, dst_points)
    warped_roi = cv.warpPerspective(roi, M, (w, h))

    return warped_roi



def bird_eye_calibrate(roi):
    h, w = roi.shape

    tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = get_warp_points_trackbars()

    tl = (tl_x, tl_y)
    tr = (tr_x, tr_y)
    bl = (bl_x, bl_y)
    br = (br_x, br_y)

    cv.circle(roi, tl, 5, (255, 255, 255), 1)
    cv.circle(roi, tr, 5, (255, 255, 255), 1)
    cv.circle(roi, bl, 5, (255, 255, 255), 1)
    cv.circle(roi, br, 5, (255, 255, 255), 1)

    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([[0, 0], [0, 20], [330, 0], [330, 20]])

    M = cv.getPerspectiveTransform(pts1, pts2)
    return tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y