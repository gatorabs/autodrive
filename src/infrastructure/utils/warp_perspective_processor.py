import numpy as np
import cv2 as cv

def get_warp_points_from_controls(ctrl):
    return (
        ctrl["tl_x"], ctrl["tl_y"],
        ctrl["tr_x"], ctrl["tr_y"],
        ctrl["bl_x"], ctrl["bl_y"],
        ctrl["br_x"], ctrl["br_y"]
    )

def bird_eye_full(frame, warp_points, draw_on=None):
    h, w = frame.shape[:2]

    tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = warp_points

    tl = (tl_x, tl_y)
    tr = (tr_x, tr_y)
    bl = (bl_x, bl_y)
    br = (br_x, br_y)

    if draw_on is not None:
        for pt in [tl, tr, bl, br]:
            cv.circle(draw_on, pt, 4, (255, 0, 0), -1)

    # Define a largura e altura da nova perspectiva baseada na distância entre pontos
    width_top = np.linalg.norm(np.array(tr) - np.array(tl))
    width_bottom = np.linalg.norm(np.array(br) - np.array(bl))
    height_left = np.linalg.norm(np.array(bl) - np.array(tl))
    height_right = np.linalg.norm(np.array(br) - np.array(tr))

    max_width = int(max(width_top, width_bottom))
    max_height = int(max(height_left, height_right))

    # Pontos de origem e destino
    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([
        [0, 0],
        [0, max_height],
        [max_width, 0],
        [max_width, max_height]
    ])

    M = cv.getPerspectiveTransform(pts1, pts2)
    warped = cv.warpPerspective(frame, M, (max_width, max_height))

    return warped
