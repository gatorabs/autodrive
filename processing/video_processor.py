import cv2 as cv
import time


class VideoProcessor:
    def __init__(self, video_source, frame_width, frame_height):
        self.video_source = video_source
        self.cap = cv.VideoCapture(video_source)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.prev_time = time.time()
        self.is_video = isinstance(video_source, str)  # Verifica se é um arquivo de vídeo

    def get_frame(self):
        ret, frame = self.cap.read()

        # Se for um vídeo e chegou ao final, reinicia
        if not ret:
            if self.is_video:
                self.cap.set(cv.CAP_PROP_POS_FRAMES, 0)  # Reinicia o vídeo
                ret, frame = self.cap.read()  # Tenta ler novamente
                if not ret:
                    raise Exception("Erro ao reiniciar o vídeo")
            else:
                raise Exception("Erro ao capturar frame")

        frame = cv.resize(frame, (self.frame_width, self.frame_height))

        # Cálculo de FPS
        current_time = time.time()
        fps = 1.0 / (current_time - self.prev_time)
        self.prev_time = current_time
        return frame, fps

    def release(self):
        self.cap.release()
