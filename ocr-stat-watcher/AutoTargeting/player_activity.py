import cv2
import numpy as np

from AutoTargeting.config import CONFIG


def has_player_activity(frame: np.ndarray, previous_frame: np.ndarray | None) -> bool:
    if previous_frame is None:
        return False

    for region in CONFIG.ignore_regions:
        if _changed_pixels(frame, previous_frame, region) >= CONFIG.player_activity_min_pixels:
            return True
    return False


def _changed_pixels(
    frame: np.ndarray,
    previous_frame: np.ndarray,
    region: tuple[int, int, int, int],
) -> int:
    x, y, width, height = region
    current_crop = frame[y : y + height, x : x + width]
    previous_crop = previous_frame[y : y + height, x : x + width]
    if current_crop.size == 0 or previous_crop.size == 0:
        return 0

    current_gray = cv2.cvtColor(current_crop, cv2.COLOR_BGR2GRAY)
    previous_gray = cv2.cvtColor(previous_crop, cv2.COLOR_BGR2GRAY)
    delta = cv2.absdiff(current_gray, previous_gray)
    _, mask = cv2.threshold(delta, CONFIG.player_activity_threshold, 255, cv2.THRESH_BINARY)
    return int(cv2.countNonZero(mask))
