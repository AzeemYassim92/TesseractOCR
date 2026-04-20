import numpy as np
import time
from config import CAPTURE

try:
    import dxcam
except ImportError:  # pragma: no cover - optional Windows backend
    dxcam = None

import mss


class ScreenCapture:
    def __init__(self) -> None:
        self._camera = None
        self._sct = mss.mss()
        self._dxcam_warned = False
        if CAPTURE.prefer_dxcam and dxcam is not None:
            self._start_dxcam()
        backend = "dxcam" if self._camera is not None else "mss"
        print(f"Capture backend: {backend}")

    def _start_dxcam(self) -> None:
        try:
            camera = dxcam.create(output_color="BGR")
            if camera is None:
                return
            camera.start(target_fps=30, video_mode=True)
            self._camera = camera
        except Exception as exc:
            self._camera = None
            if not self._dxcam_warned:
                print(f"dxcam start failed; falling back to mss. Error: {exc}")
                self._dxcam_warned = True

    def _restart_dxcam(self) -> None:
        old_camera = self._camera
        self._camera = None
        if old_camera is not None:
            try:
                old_camera.stop()
            except Exception:
                pass
        self._start_dxcam()

    def grab_region(self, region: dict) -> np.ndarray:
        if self._camera is not None:
            left = region["left"]
            top = region["top"]
            right = left + region["width"]
            bottom = top + region["height"]

            try:
                for _ in range(5):
                    frame = self._camera.get_latest_frame()
                    if frame is not None:
                        frame_height, frame_width = frame.shape[:2]
                        if 0 <= left < right <= frame_width and 0 <= top < bottom <= frame_height:
                            return frame[top:bottom, left:right].copy()
                        break
                    time.sleep(0.02)
            except Exception as exc:
                print(f"dxcam read failed; restarting camera. Error: {exc}")
                self._restart_dxcam()
                time.sleep(0.05)
                return self.grab_region(region)

            print("dxcam returned no frame; restarting camera.")
            self._restart_dxcam()
            time.sleep(0.05)
            if self._camera is not None:
                return self.grab_region(region)

        shot = self._sct.grab(region)
        img = np.array(shot)
        # BGRA -> BGR
        return img[:, :, :3]
