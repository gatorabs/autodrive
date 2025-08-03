import numpy as np


def calculate_center_distance(img, interval):
    """Calculate average distances from the image center to lane markers.

    Additionally collects the line segments used for each sampled row so that
    they can be visualised later.
    """
    height, width = img.shape
    center_x = width // 2
    left_distances = []
    right_distances = []
    left_lines = []
    right_lines = []

    for i in range(0, height, interval):
        row = img[i, :]

        right_indices = np.where(row[center_x:] >= 50)[0]
        if right_indices.size > 0:
            dist_right = right_indices[0]
            right_distances.append(dist_right)
            right_x = center_x + dist_right
            right_lines.append(((center_x, i), (right_x, i)))

        left_indices = np.where(row[:center_x + 1] >= 50)[0]
        if left_indices.size > 0:
            dist_left = center_x - left_indices[-1]
            left_distances.append(dist_left)
            left_x = left_indices[-1]
            left_lines.append(((center_x, i), (left_x, i)))

    avg_left = np.mean(left_distances) if left_distances else float('inf')
    avg_right = np.mean(right_distances) if right_distances else float('inf')

    return avg_left, avg_right, left_lines, right_lines
