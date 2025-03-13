import cv2

def object_detector_trackbar_process(shared_controls):
    window_name = "Object Detector Trackbars"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Valores iniciais e limites
    initial_target = shared_controls.get("TARGET_BOX_HEIGHT")
    initial_tol = shared_controls.get("TOLERANCE")

    cv2.createTrackbar("Target Height", window_name, initial_target, 500, lambda x: None)
    cv2.createTrackbar("Tolerance", window_name, initial_tol, 100, lambda x: None)

    while True:
        target = cv2.getTrackbarPos("Target Height", window_name)
        tol = cv2.getTrackbarPos("Tolerance", window_name)
        shared_controls["TARGET_BOX_HEIGHT"] = target
        shared_controls["TOLERANCE"] = tol

        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
    cv2.destroyWindow(window_name)
