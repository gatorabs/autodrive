import cv2 as cv


def create_control_window():
    cv.namedWindow('Controls')
    cv.createTrackbar('F_Canny', 'Controls', 20, 300, lambda x: None)
    cv.createTrackbar('S_Canny', 'Controls', 152, 400, lambda x: None)
    cv.createTrackbar('Speed', 'Controls', 1, 255, lambda x: None)
    cv.createTrackbar('Side', 'Controls', 1, 1, lambda x: None)

    # Trackbars para o PID (com escala 1000)
    cv.createTrackbar('KP', 'Controls', int(0.3 * 1000), 1000, lambda x: None)
    cv.createTrackbar('KI', 'Controls', int(0.005 * 1000), 100, lambda x: None)
    cv.createTrackbar('KD', 'Controls', int(0.01 * 1000), 500, lambda x: None)


def get_trackbar_values():
    canny_1 = cv.getTrackbarPos('F_Canny', 'Controls')
    canny_2 = cv.getTrackbarPos('S_Canny', 'Controls')
    speed = cv.getTrackbarPos('Speed', 'Controls')
    side = cv.getTrackbarPos('Side', 'Controls')

    kp = cv.getTrackbarPos('KP', 'Controls') / 1000.0
    ki = cv.getTrackbarPos('KI', 'Controls') / 1000.0
    kd = cv.getTrackbarPos('KD', 'Controls') / 1000.0

    return canny_1, canny_2, speed, side, kp, ki, kd
