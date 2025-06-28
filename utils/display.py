import cv2 as cv
import numpy as np


def draw_overlays(frame, distances, warp_points=None, edges=None):
    if not hasattr(draw_overlays, "font_props"):
        draw_overlays.font_props = {
            "font": cv.QT_FONT_NORMAL,
            "scale": 0.5,
            "color": (0, 255, 255),
            "thickness": 1
        }

    font = draw_overlays.font_props["font"]
    font_scale = draw_overlays.font_props["scale"]
    font_color = draw_overlays.font_props["color"]
    thickness = draw_overlays.font_props["thickness"]

    overlay = frame.copy()

    # --- Desenhar área da perspectiva e pintar faixas de amarelo ---
    if warp_points and edges is not None:
        # Extrair pontos do warp
        tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = warp_points
        pts = np.array([[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]], np.int32).reshape((-1, 1, 2))

        # Máscara binária da área de interesse
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv.fillPoly(mask, [pts], 255)

        # Pintar os pontos das bordas (edges == 255) dentro da região com amarelo
        yellow = (0, 255, 255)
        edge_mask = cv.bitwise_and(edges, edges, mask=mask)
        frame[edge_mask == 255] = yellow

        # Desenhar transparência verde da perspectiva
        cv.fillPoly(overlay, [pts], (0, 255, 0))
        alpha = 0.3
        frame = cv.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Desenhar contorno do polígono
        cv.polylines(frame, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

        # --- DESENHAR FASOR DE DESBALANÇO ---
        avg_left, avg_right = distances

        if avg_left != float('inf') and avg_right != float('inf'):
            mid_y = (tl_y + tr_y) // 2 + 50  # altura média + deslocamento
            center_x = (tl_x + tr_x) // 2

            # Define o vetor em relação ao centro da imagem (direita - esquerda)
            magnitude = int(avg_right - avg_left)
            fasor_length = max(min(magnitude * 2, 100), -100)  # limitar o tamanho do vetor
            end_point = (center_x + fasor_length, mid_y)

            # Desenha o vetor como uma seta
            cv.arrowedLine(frame, (center_x, mid_y), end_point, (0, 0, 255), 2, tipLength=0.1)

            # Texto com os valores
            cv.putText(frame, f"L: {avg_left:.1f} R: {avg_right:.1f}", (center_x - 60, mid_y - 10),
                       font, font_scale, font_color, thickness)

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