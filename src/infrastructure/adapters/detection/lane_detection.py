import numpy as np


def calculate_center_distance(img, interval):
    height, width = img.shape
    center_x = width // 2
    left_distances = []
    right_distances = []

    for i in range(0, height, interval):
        row = img[i, :]

        right_indices = np.where(row[center_x:] >= 50)[0]
        if right_indices.size > 0:
            right_distances.append(right_indices[0])

        left_indices = np.where(row[:center_x + 1] >= 50)[0]
        if left_indices.size > 0:
            left_distances.append(center_x - left_indices[-1])

    avg_left = np.mean(left_distances) if left_distances else float('inf')
    avg_right = np.mean(right_distances) if right_distances else float('inf')

    return avg_left, avg_right
