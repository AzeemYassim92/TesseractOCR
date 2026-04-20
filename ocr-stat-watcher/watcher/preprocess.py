import cv2
import numpy as np


def preprocess_for_ocr(image: np.ndarray, upscale_factor: int, threshold_value: int) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    enlarged = cv2.resize(
        gray,
        None,
        fx=upscale_factor,
        fy=upscale_factor,
        interpolation=cv2.INTER_CUBIC,
    )

    blurred = cv2.GaussianBlur(enlarged, (3, 3), 0)
    _, binary = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY)

    # Drop scanline-style UI artifacts that span most of the crop width.
    row_counts = np.count_nonzero(binary, axis=1)
    wide_row_threshold = int(binary.shape[1] * 0.5)
    binary[row_counts > wide_row_threshold, :] = 0

    # Keep only meaningful glyph components and discard tiny fragments.
    component_map = (binary > 0).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(component_map, connectivity=8)
    cleaned = np.zeros_like(binary)
    for label_index in range(1, num_labels):
        _, _, _, _, area = stats[label_index]
        if area < 12:
            continue
        cleaned[labels == label_index] = 255

    bordered = cv2.copyMakeBorder(
        cleaned,
        12,
        12,
        12,
        12,
        cv2.BORDER_CONSTANT,
        value=0,
    )
    return bordered
