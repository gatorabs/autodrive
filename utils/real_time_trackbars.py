import cv2 as cv
from utils.constants import tl,tr,bl,br

def create_warp_points_trackbars():
    cv.namedWindow('Points')
    cv.createTrackbar('tl x', 'Points', tl[0], 320, lambda x: None)
    cv.createTrackbar('tl y', 'Points', tl[1], 20, lambda x: None)

    cv.createTrackbar('tr x', 'Points', tr[0], 320, lambda x: None)
    cv.createTrackbar('tr y', 'Points', tr[1], 20, lambda x: None)

    cv.createTrackbar('bl x', 'Points', bl[0], 320, lambda x: None)
    cv.createTrackbar('bl y', 'Points', bl[1], 20, lambda x: None)

    cv.createTrackbar('br x', 'Points', br[0], 320, lambda x: None)
    cv.createTrackbar('br y', 'Points', br[1], 20, lambda x: None)

def get_warp_points_trackbars():
    tl_x = cv.getTrackbarPos('tl x', 'Points')
    tl_y = cv.getTrackbarPos('tl y', 'Points')

    tr_x = cv.getTrackbarPos('tr x', 'Points')
    tr_y = cv.getTrackbarPos('tr y', 'Points')

    bl_x = cv.getTrackbarPos('bl x', 'Points')
    bl_y = cv.getTrackbarPos('bl y', 'Points')

    br_x = cv.getTrackbarPos('br x', 'Points')
    br_y = cv.getTrackbarPos('br y', 'Points')

    return tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y