import numpy as np
import cv2 as cv


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
