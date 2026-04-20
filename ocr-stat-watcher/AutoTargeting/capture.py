import numpy as np
import mss


class RegionCapture:
    def __init__(self) -> None:
        self._sct = mss.mss()

    def grab(self, region: tuple[int, int, int, int]) -> np.ndarray:
        left, top, width, height = region
        shot = self._sct.grab(
            {
                "left": left,
                "top": top,
                "width": width,
                "height": height,
            }
        )
        image = np.array(shot)
        return image[:, :, :3]
