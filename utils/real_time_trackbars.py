import cv2 as cv
from utils.constants import tl,tr,bl,br

def create_warp_points_trackbars(width, height):
    cv.namedWindow('Points', cv.WINDOW_NORMAL)

    cv.createTrackbar('tl x', 'Points', 0, width - 1, lambda x: None)
    cv.createTrackbar('tl y', 'Points', 0, height - 1, lambda x: None)

    cv.createTrackbar('tr x', 'Points', width - 1, width - 1, lambda x: None)
    cv.createTrackbar('tr y', 'Points', 0, height - 1, lambda x: None)

    cv.createTrackbar('bl x', 'Points', 0, width - 1, lambda x: None)
    cv.createTrackbar('bl y', 'Points', height - 1, height - 1, lambda x: None)

    cv.createTrackbar('br x', 'Points', width - 1, width - 1, lambda x: None)
    cv.createTrackbar('br y', 'Points', height - 1, height - 1, lambda x: None)


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

def recreate_warp_trackbar_window(roi_width, roi_height):
    try:
        cv.destroyWindow('Points')
    except:
        pass
    create_warp_points_trackbars(roi_width, roi_height)
