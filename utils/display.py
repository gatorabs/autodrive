import cv2 as cv
import numpy as np
from utils.constants import YELLOW,RESET,GREEN

def draw_overlays(frame, roi_coords, roi_x_coords, distances, frame_center):
    # Cache das propriedades de fonte para evitar redefinições
    if not hasattr(draw_overlays, "font_props"):
        draw_overlays.font_props = {
            "font": cv.FONT_HERSHEY_SIMPLEX,
            "scale": 0.5,
            "color": (0, 255, 255),
            "thickness": 1
        }

    font = draw_overlays.font_props["font"]
    font_scale = draw_overlays.font_props["scale"]
    font_color = draw_overlays.font_props["color"]
    thickness = draw_overlays.font_props["thickness"]

    avg_left, avg_right = distances
    roi_start, roi_end = roi_coords
    roi_x_start, roi_x_end = roi_x_coords

    overlay = frame.copy()
    overlay_color = (0, 255, 0)
    alpha = 0.3

    # Retângulo semi-transparente sobre a ROI
    cv.rectangle(overlay, (roi_x_start, roi_start), (roi_x_end, roi_end), overlay_color, -1)
    frame = cv.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Desenha retângulo para o lado direito
    if avg_right != float('inf'):
        top_left = (frame_center, roi_start)
        bottom_right = (frame_center + int(avg_right), roi_end)
        cv.rectangle(frame, top_left, bottom_right, (0, 255, 255), 2)
        cv.putText(frame, f"{avg_right:.1f}", (frame_center + 30, roi_start - 10),
                   font, font_scale, font_color, thickness, cv.LINE_AA)

    # Desenha retângulo para o lado esquerdo
    if avg_left != float('inf'):
        top_left = (frame_center - int(avg_left), roi_start)
        bottom_right = (frame_center, roi_end)
        cv.rectangle(frame, top_left, bottom_right, (0, 255, 255), 2)
        cv.putText(frame, f"{avg_left:.1f}", (frame_center - 60, roi_start - 10),
                   font, font_scale, font_color, thickness, cv.LINE_AA)

    # Linha central
    #cv.line(frame, (frame_center, 0), (frame_center, frame.shape[0]), (255, 255, 255), 2)

    # Exibe FPS (print limitado em produção)
    #if show_fps:
        #cv.putText(frame, f"FPS: {fps:.2f}", (10, 30), font, 0.7, (0, 255, 0), 2, cv.LINE_AA)
        #cv.putText(frame, f"MS: {avg_time:.2f}", (10,70), font, 0.7, (0,255,0), 2, cv.LINE_AA)

    return frame


def create_main_window(video_img, edges_img, roi_img, show_video=True, show_edges=True, show_roi=True):
    reference = next((img for img in [video_img, edges_img, roi_img] if img is not None), None)
    if reference is None:
        reference = np.zeros((480, 640, 3), dtype=np.uint8)

    height, width = reference.shape[:2]

    # Cache da imagem branca
    if not hasattr(create_main_window, "blank") or \
       create_main_window.blank.shape[:2] != (height, width):
        create_main_window.blank = np.zeros((height, width, 3), dtype=np.uint8)

    blank = create_main_window.blank

    # Escolhe qual imagem mostrar ou substitui por branco
    def prepare_image(img, show_flag):
        if not show_flag or img is None:
            return blank
        if img.ndim == 2:  # Grayscale
            img = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
        if img.shape[0] != height:
            img = cv.resize(img, (img.shape[1], height))
        return img

    video_disp = prepare_image(video_img, show_video)
    edges_disp = prepare_image(edges_img, show_edges)
    roi_disp   = prepare_image(roi_img,   show_roi)

    # Concatena horizontalmente
    main_window = cv.hconcat([video_disp, edges_disp, roi_disp])
    return main_window