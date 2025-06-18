import numpy as np
import cv2 as cv

def get_warp_points_from_controls(ctrl):
    return (
        ctrl["tl_x"], ctrl["tl_y"],
        ctrl["tr_x"], ctrl["tr_y"],
        ctrl["bl_x"], ctrl["bl_y"],
        ctrl["br_x"], ctrl["br_y"]
    )

def bird_eye(roi, warp_points, draw_on=None, offset_x=0, offset_y=0):
    h, w = roi.shape[:2]

    tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = warp_points

    tl = (tl_x, tl_y)
    tr = (tr_x, tr_y)
    bl = (bl_x, bl_y)
    br = (br_x, br_y)

    if draw_on is not None:
        for pt in [tl, tr, bl, br]:
            x, y = pt[0] + offset_x, pt[1] + offset_y
            cv.circle(draw_on, (x, y), 2, (255, 0, 255), -1)

    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([[0, 0], [0, h], [w, 0], [w, h]])

    M = cv.getPerspectiveTransform(pts1, pts2)
    warped_roi = cv.warpPerspective(roi, M, (w, h))

    return warped_roi
