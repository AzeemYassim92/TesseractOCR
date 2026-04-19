import time
from collections import deque

from config import OCR, TIMINGS
from regions import HP_REGION, MP_REGION
from watcher.capture import ScreenCapture
from watcher.preprocess import preprocess_for_ocr
from watcher.ocr_reader import read_text
from watcher.parser import parse_stat_pair
from watcher.triggers import TriggerController


def stable_value(history: deque):
    if len(history) < TIMINGS.stable_reads_required:
        return None

    values = list(history)
    if all(v == values[0] for v in values):
        return values[0]
    return None


def main() -> None:
    capturer = ScreenCapture()
    trigger = TriggerController()

    hp_history = deque(maxlen=TIMINGS.stable_reads_required)
    mp_history = deque(maxlen=TIMINGS.stable_reads_required)

    print("Starting OCR stat watcher. Press Ctrl+C to stop.")

    while True:
        hp_raw = capturer.grab_region(HP_REGION)
        mp_raw = capturer.grab_region(MP_REGION)

        hp_pre = preprocess_for_ocr(hp_raw, OCR.upscale_factor, OCR.threshold_value)
        mp_pre = preprocess_for_ocr(mp_raw, OCR.upscale_factor, OCR.threshold_value)

        hp_text = read_text(hp_pre)
        mp_text = read_text(mp_pre)

        hp_pair = parse_stat_pair(hp_text)
        mp_pair = parse_stat_pair(mp_text)

        print(f"HP OCR={hp_text!r} parsed={hp_pair} | MP OCR={mp_text!r} parsed={mp_pair}")

        if hp_pair is not None:
            hp_history.append(hp_pair)
        if mp_pair is not None:
            mp_history.append(mp_pair)

        stable_hp = stable_value(hp_history)
        stable_mp = stable_value(mp_history)

        if stable_hp is not None and stable_mp is not None:
            hp_current, _ = stable_hp
            mp_current, _ = stable_mp
            trigger.evaluate(hp_current=hp_current, mp_current=mp_current)

        time.sleep(TIMINGS.poll_interval_seconds)


if __name__ == "__main__":
    main()
