import cv2
import time

class VideoProcessor:
    def __init__(self, video_source, frame_width, frame_height):
        self.video_source = video_source
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.prev_time = time.time()

        # Detecta se é uma câmera (índice inteiro)
        if isinstance(video_source, str) and video_source.isdigit():
            self.is_video = False
            self.cap = cv2.VideoCapture(int(video_source), cv2.CAP_DSHOW)
        elif isinstance(video_source, int):
            self.is_video = False
            self.cap = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
        else:
            self.is_video = True
            self.cap = cv2.VideoCapture(video_source)

        if not self.cap.isOpened():
            raise Exception(f"Não foi possível abrir a fonte de vídeo: {video_source}")

    def get_frame(self):
        ret, frame = self.cap.read()

        # Se for um vídeo e chegou ao final, reinicia
        if not ret:
            if self.is_video:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    raise Exception("Erro ao reiniciar o vídeo")
            else:
                raise Exception("Erro ao capturar frame da câmera")

        frame = cv2.resize(frame, (self.frame_width, self.frame_height))
        return frame

    def release(self):
        self.cap.release()
