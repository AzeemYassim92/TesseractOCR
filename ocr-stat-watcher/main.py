import time
from collections import deque

import cv2
import numpy as np

from config import OCR, TIMINGS
from regions import HP_REGION, MP_REGION
from watcher.capture import ScreenCapture
from watcher.debug import save_debug_image
from watcher.preprocess import preprocess_for_ocr
from watcher.ocr_reader import read_digit_components, read_digits, read_text
from watcher.parser import parse_stat_pair
from watcher.triggers import TriggerController
from watcher.warehouse import WarehouseRunner


def stable_value(history: deque):
    if len(history) < TIMINGS.stable_reads_required:
        return None

    values = list(history)
    max_values = {max_value for _, max_value in values}
    if len(max_values) != 1:
        return None

    return values[-1]


def detect_slash_bounds(image: np.ndarray):
    component_map = (image > 0).astype(np.uint8)
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(component_map, connectivity=8)
    if num_labels <= 1:
        return None

    components = []
    max_height = 0
    for label_index in range(1, num_labels):
        x, y, width, height, area = stats[label_index]
        max_height = max(max_height, height)
        components.append((x, y, width, height, area))

    glyph_components = [component for component in components if component[3] >= int(max_height * 0.7)]
    if len(glyph_components) < 3:
        return None

    glyph_components.sort(key=lambda component: component[0])
    interior_components = glyph_components[1:-1]
    if not interior_components:
        return None

    slash = min(interior_components, key=lambda component: component[2])
    slash_x, _, slash_width, _, _ = slash
    return slash_x, slash_x + slash_width


def split_stat_image(raw_image: np.ndarray, preprocessed_image: np.ndarray):
    slash_bounds = detect_slash_bounds(preprocessed_image)
    if slash_bounds is None:
        return None

    slash_left, slash_right = slash_bounds
    border_size = 12
    raw_slash_left = max((slash_left - border_size) // OCR.upscale_factor, 1)
    raw_slash_right = min((slash_right - border_size + OCR.upscale_factor - 1) // OCR.upscale_factor, raw_image.shape[1] - 1)

    gap = 1
    left_end = max(raw_slash_left - gap, 1)
    right_start = min(raw_slash_right + gap, raw_image.shape[1] - 1)
    return raw_image[:, :left_end], raw_image[:, right_start:]


def fallback_parse_stat_pair(raw_image: np.ndarray, preprocessed_image: np.ndarray):
    split_images = split_stat_image(raw_image, preprocessed_image)
    if split_images is None:
        return None, None, None

    current_raw, max_raw = split_images
    current_pre = preprocess_for_ocr(current_raw, OCR.upscale_factor, OCR.threshold_value)
    max_pre = preprocess_for_ocr(max_raw, OCR.upscale_factor, OCR.threshold_value)

    current_text = read_digit_components(current_pre) or read_digits(current_pre)
    max_text = read_digit_components(max_pre) or read_digits(max_pre)

    if not current_text or not max_text:
        return None, current_pre, max_pre

    current_value = int(current_text)
    max_value = int(max_text)
    if current_value < 0 or max_value <= 0 or current_value > max_value:
        return None, current_pre, max_pre

    return (current_value, max_value), current_pre, max_pre


def parse_stat_from_images(raw_image: np.ndarray, preprocessed_image: np.ndarray, prefix: str):
    split_pair, current_pre, max_pre = fallback_parse_stat_pair(raw_image, preprocessed_image)
    if split_pair is not None:
        save_debug_image(f"{prefix}_current_pre.png", current_pre)
        save_debug_image(f"{prefix}_max_pre.png", max_pre)
        return split_pair, "split", ""

    full_text = read_text(preprocessed_image)
    full_pair = parse_stat_pair(full_text)
    if full_pair is not None:
        return full_pair, "full", full_text

    save_debug_image(f"{prefix}_parse_failed_pre.png", preprocessed_image)
    return None, "none", full_text


def main() -> None:
    capturer = ScreenCapture()
    trigger = TriggerController()
    warehouse = WarehouseRunner()
    warehouse.install_hotkeys()

    hp_history = deque(maxlen=TIMINGS.stable_reads_required)
    mp_history = deque(maxlen=TIMINGS.stable_reads_required)

    print("Starting OCR stat watcher. Press Ctrl+C to stop.")

    try:
        while True:
            hp_raw = capturer.grab_region(HP_REGION)
            mp_raw = capturer.grab_region(MP_REGION)
            save_debug_image("hp_raw.png", hp_raw)
            save_debug_image("mp_raw.png", mp_raw)

            hp_pre = preprocess_for_ocr(hp_raw, OCR.upscale_factor, OCR.threshold_value)
            mp_pre = preprocess_for_ocr(mp_raw, OCR.upscale_factor, OCR.threshold_value)
            save_debug_image("hp_pre.png", hp_pre)
            save_debug_image("mp_pre.png", mp_pre)

            hp_pair, hp_source, hp_text = parse_stat_from_images(hp_raw, hp_pre, "hp")
            mp_pair, mp_source, mp_text = parse_stat_from_images(mp_raw, mp_pre, "mp")

            print(
                f"HP OCR={hp_text!r} parsed={hp_pair} source={hp_source} | "
                f"MP OCR={mp_text!r} parsed={mp_pair} source={mp_source}"
            )

            if hp_pair is not None:
                hp_history.append(hp_pair)
            else:
                hp_history.clear()

            if mp_pair is not None:
                mp_history.append(mp_pair)
            else:
                mp_history.clear()

            stable_hp = stable_value(hp_history)
            stable_mp = stable_value(mp_history)

            hp_current = stable_hp[0] if stable_hp is not None else None
            mp_current = stable_mp[0] if stable_mp is not None else None
            if hp_current is not None or mp_current is not None:
                trigger.evaluate(hp_current=hp_current, mp_current=mp_current)

            time.sleep(TIMINGS.poll_interval_seconds)
    finally:
        warehouse.uninstall_hotkeys()


if __name__ == "__main__":
    main()
