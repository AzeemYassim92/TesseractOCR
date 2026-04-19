import numpy as np
import mss


class ScreenCapture:
    def __init__(self) -> None:
        self._sct = mss.mss()

    def grab_region(self, region: dict) -> np.ndarray:
        shot = self._sct.grab(region)
        img = np.array(shot)
        # BGRA -> BGR
        return img[:, :, :3]
