import cv2

def publish(frame, shared_frames):
    _, buffer = cv2.imencode('.jpg', frame)
    shared_frames["TAB2_FRAME"] = buffer.tobytes()