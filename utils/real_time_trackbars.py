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


def get_control_trackbar_values():
    canny_1 = cv.getTrackbarPos('F_Canny', 'Controls')
    canny_2 = cv.getTrackbarPos('S_Canny', 'Controls')
    speed = cv.getTrackbarPos('Speed', 'Controls')
    side = cv.getTrackbarPos('Side', 'Controls')

    kp = cv.getTrackbarPos('KP', 'Controls') / 1000.0
    ki = cv.getTrackbarPos('KI', 'Controls') / 1000.0
    kd = cv.getTrackbarPos('KD', 'Controls') / 1000.0

    return canny_1, canny_2, speed, side, kp, ki, kd

def create_object_roi_control_window():
    cv.namedWindow('ROI')
    cv.createTrackbar('Person', 'ROI', 0, 240, lambda x: None)
    cv.createTrackbar('Traffic', 'ROI', 0, 240, lambda x: None)

def get_object_roi_trackbar_values():
    person = cv.getTrackbarPos('Person', 'ROI')
    traffic = cv.getTrackbarPos('Traffic', 'ROI')

    return person, traffic

def create_roi_trackbars(window_name, frame_width, frame_height,
                       init_start=200, init_end=220,
                       init_x_start=80, init_x_end=400):

    cv.namedWindow("ROI_C", cv.WINDOW_NORMAL)
    cv.createTrackbar("ROI_START", window_name, init_start, frame_height, lambda v: None)
    cv.createTrackbar("ROI_END", window_name, init_end, frame_height, lambda v: None)
    cv.createTrackbar("ROI_X_START", window_name, init_x_start, frame_width, lambda v: None)
    cv.createTrackbar("ROI_X_END", window_name, init_x_end, frame_width, lambda v: None)


def get_roi_trackbars(frame_width, frame_height):

    y_start = cv.getTrackbarPos("ROI_START", "ROI_C")
    y_end = cv.getTrackbarPos("ROI_END", "ROI_C")
    x_start = cv.getTrackbarPos("ROI_X_START", "ROI_C")
    x_end = cv.getTrackbarPos("ROI_X_END", "ROI_C")

    # Clamp e validação
    y_start = min(max(0, y_start), frame_height - 1)
    y_end = min(max(y_start + 1, y_end), frame_height)
    x_start = min(max(0, x_start), frame_width - 1)
    x_end = min(max(x_start + 1, x_end), frame_width)

    return y_start, y_end, x_start, x_end
