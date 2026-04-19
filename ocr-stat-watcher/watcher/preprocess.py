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

    _, binary = cv2.threshold(enlarged, threshold_value, 255, cv2.THRESH_BINARY)
    return binary
