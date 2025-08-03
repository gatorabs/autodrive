import cv2 as cv
import numpy as np
import math


def draw_overlays(frame, distances, warp_points=None, edges=None,
                  has_ref=False, show_info=None, fps=0, ms=0, mapped_direction=90,
                  roi=None, left_lines=None, right_lines=None, show_roi_lines=False):
    if not hasattr(draw_overlays, "font_props"):
        draw_overlays.font_props = {
            "font": cv.QT_FONT_NORMAL,
            "scale": 0.5,
            "color": (0, 255, 255),
            "thickness": 1,
            "wheel-thickness": 4
        }

    font = draw_overlays.font_props["font"]
    font_scale = draw_overlays.font_props["scale"]
    font_color = draw_overlays.font_props["color"]
    thickness = draw_overlays.font_props["thickness"]
    wheel_thickness = draw_overlays.font_props["wheel-thickness"]

    overlay = frame.copy()
    roi_display = None

    # área de perspectiva e faixas amarelas.
    if warp_points and edges is not None:
        tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = warp_points
        pts = np.array([[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]],
                       np.int32).reshape((-1, 1, 2))

        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv.fillPoly(mask, [pts], 255)
        edge_mask = cv.bitwise_and(edges, edges, mask=mask)
        frame[edge_mask == 255] = (0, 255, 255)
        cv.fillPoly(overlay, [pts], (0, 255, 0))
        frame = cv.addWeighted(overlay, 0.3, frame, 0.7, 0)
        cv.polylines(frame, [pts], True, (255, 0, 0), 2)

        avg_left, avg_right = distances

        if has_ref:
            # posição central fixa para o volante
            center_x = (tl_x + tr_x) // 2
            mid_y = (tl_y + tr_y) // 2 + 50

            # 1) volante (círculo externo)
            radius = 40
            wheel_color = (200, 200, 200)
            cv.circle(frame, (center_x, mid_y), radius, wheel_color, wheel_thickness)

            # 2) volante giratório: spokes mais grossos
            num_spokes = 3
            length = int(radius * 0.9)
            for i in range(num_spokes):
                offset = i * (360 / num_spokes)
                spoke_angle = (mapped_direction - 90.0) + offset
                rad = math.radians(spoke_angle)
                end_x = int(center_x + length * math.sin(rad))
                end_y = int(mid_y - length * math.cos(rad))
                cv.line(frame,
                        (center_x, mid_y),
                        (end_x, end_y),
                        wheel_color,
                        wheel_thickness)

            # 3) opcional: texto com os valores de L e R
            cv.putText(frame,
                       f"L:{avg_left:.1f} R:{avg_right:.1f}",
                       (center_x - 60, mid_y - radius - 10),
                       font, font_scale, font_color, thickness)

        if roi is not None and show_roi_lines:
            if len(roi.shape) == 2:
                roi_display = cv.cvtColor(roi, cv.COLOR_GRAY2BGR)
            else:
                roi_display = roi.copy()

            roi_h, roi_w = roi_display.shape[:2]
            pts1 = np.float32([[tl_x, tl_y], [bl_x, bl_y], [tr_x, tr_y], [br_x, br_y]])
            pts2 = np.float32([[0, 0], [0, roi_h], [roi_w, 0], [roi_w, roi_h]])
            inv_M = cv.getPerspectiveTransform(pts2, pts1)

            def draw_line_set(lines, color):
                for start, end in lines:
                    pts = np.array([start, end], dtype=np.float32).reshape(-1, 1, 2)
                    transformed = cv.perspectiveTransform(pts, inv_M).reshape(-1, 2)
                    start_t = tuple(np.int32(transformed[0]))
                    end_t = tuple(np.int32(transformed[1]))
                    cv.line(frame, start_t, end_t, color, 1)

            if left_lines:
                draw_line_set(left_lines, (255, 0, 0))
            if right_lines:
                draw_line_set(right_lines, (0, 255, 0))

        if show_info:
            debug_lines = [
                f"Mapped Dir: {mapped_direction}",
                f"FPS: {fps:.1f}",
                f"MS: {ms:.1f}",
                f"Ref Detected: {has_ref}"
            ]

            # Propriedades da caixa
            x, y = 10, 10
            line_height = 20
            padding = 5
            box_width = 200
            box_height = line_height * len(debug_lines) + padding * 2

            # Fundo da caixa (semitransparente)
            overlay_debug = frame.copy()
            cv.rectangle(overlay_debug,
                         (x, y),
                         (x + box_width, y + box_height),
                         (50, 50, 50),
                         cv.FILLED)
            frame = cv.addWeighted(overlay_debug, 0.5, frame, 0.5, 0)

            for i, text in enumerate(debug_lines):
                text_y = y + padding + (i + 1) * line_height - 5
                cv.putText(frame,
                           text,
                           (x + padding, text_y),
                           font, font_scale, font_color, thickness)

    return frame
