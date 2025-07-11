import cv2 as cv

def toggle_named_window(is_enabled: bool, window_name: str, frame=None):
    if is_enabled and frame is not None:
        cv.imshow(window_name, frame)
    else:
        try:
            if cv.getWindowProperty(window_name, cv.WND_PROP_VISIBLE) >= 1:
                cv.destroyWindow(window_name)
        except cv.error:
            pass
