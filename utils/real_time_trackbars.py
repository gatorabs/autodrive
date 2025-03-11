import cv2 as cv


def create_control_window():
    cv.namedWindow('Controls')
    cv.createTrackbar('F_Canny', 'Controls', 20, 300, lambda x: None)
    cv.createTrackbar('S_Canny', 'Controls', 152, 400, lambda x: None)
    cv.createTrackbar('Speed', 'Controls', 1, 255, lambda x: None)
    cv.createTrackbar('Side', 'Controls', 1, 1, lambda x: None)

def get_trackbar_values():
    canny_1 = cv.getTrackbarPos('F_Canny', 'Controls')
    canny_2 = cv.getTrackbarPos('S_Canny', 'Controls')
    speed = cv.getTrackbarPos('Speed', 'Controls')
    side = cv.getTrackbarPos('Side', 'Controls')
    return canny_1, canny_2, speed, side

