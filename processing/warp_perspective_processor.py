import numpy as np
import cv2 as cv


def bird_eye(roi):
    h, w = roi.shape

    tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = get_trackbar()

    tl = (tl_x, tl_y)
    tr = (tr_x, tr_y)
    bl = (bl_x, bl_y)
    br = (br_x, br_y)

    cv.circle(roi, tl, 5, (255,255,255), 1)
    cv.circle(roi, tr, 5, (255,255,255), 1)
    cv.circle(roi, bl, 5, (255,255,255), 1)
    cv.circle(roi, br, 5, (255,255,255), 1)

    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np. float32([[0,0], [0,20], [330,0], [330,20]])


    M = cv.getPerspectiveTransform(pts1, pts2)
    warped_roi = cv.warpPerspective(roi, M, (w, h))

    return warped_roi


def get_trackbar():
    tl_x = cv.getTrackbarPos('tl x', 'Points')
    tl_y = cv.getTrackbarPos('tl y', 'Points')

    tr_x = cv.getTrackbarPos('tr x', 'Points')
    tr_y = cv.getTrackbarPos('tr y', 'Points')

    bl_x = cv.getTrackbarPos('bl x', 'Points')
    bl_y = cv.getTrackbarPos('bl y', 'Points')

    br_x = cv.getTrackbarPos('br x', 'Points')
    br_y = cv.getTrackbarPos('br y', 'Points')

    return tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y

def create_track():
    cv.namedWindow('Points')
    cv.createTrackbar('tl x', 'Points', 0, 320, lambda x: None)
    cv.createTrackbar('tl y', 'Points', 0, 20, lambda x: None)

    cv.createTrackbar('tr x', 'Points', 0, 320, lambda x: None)
    cv.createTrackbar('tr y', 'Points', 0, 20, lambda x: None)

    cv.createTrackbar('bl x', 'Points', 0, 320, lambda x: None)
    cv.createTrackbar('bl y', 'Points', 0, 20, lambda x: None)

    cv.createTrackbar('br x', 'Points', 0, 320, lambda x: None)
    cv.createTrackbar('br y', 'Points', 0, 20, lambda x: None)


