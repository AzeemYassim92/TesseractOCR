import threading

import numpy as np
import mss


class RegionCapture:
    def __init__(self) -> None:
        self._sct = None
        self._thread_id = None

    def grab(self, region: tuple[int, int, int, int]) -> np.ndarray:
        sct = self._capture_for_current_thread()
        left, top, width, height = region
        shot = sct.grab(
            {
                "left": left,
                "top": top,
                "width": width,
                "height": height,
            }
        )
        image = np.array(shot)
        return image[:, :, :3]

    def _capture_for_current_thread(self):
        thread_id = threading.get_ident()
        if self._sct is None or self._thread_id != thread_id:
            self._sct = mss.mss()
            self._thread_id = thread_id
        return self._sct
