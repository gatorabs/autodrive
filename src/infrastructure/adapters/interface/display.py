import cv2 as cv
import numpy as np
import math

def draw_overlays(frame, distances, warp_points=None, edges=None,
                  has_ref=False, mapped_direction=90):
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

    return frame
