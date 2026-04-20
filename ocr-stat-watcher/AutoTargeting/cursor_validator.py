from dataclasses import dataclass
from pathlib import Path
import threading

import cv2
import mss
import numpy as np

from AutoTargeting.config import CONFIG


@dataclass(frozen=True)
class CursorValidationResult:
    matched: bool
    score: float
    label: str | None
    crop_path: Path


class CursorValidator:
    def __init__(self) -> None:
        CONFIG.cursor_templates_dir.mkdir(parents=True, exist_ok=True)
        self._templates = _load_cursor_templates()
        self._sct = None
        self._thread_id = None

    @property
    def template_count(self) -> int:
        return len(self._templates)

    def validate_at(self, screen_x: int, screen_y: int) -> CursorValidationResult:
        crop = self._capture_crop(screen_x, screen_y)
        CONFIG.debug_dir.mkdir(parents=True, exist_ok=True)
        crop_path = CONFIG.debug_dir / "latest_cursor_crop.png"
        cv2.imwrite(str(crop_path), crop)

        if not CONFIG.cursor_validation_enabled:
            return CursorValidationResult(True, 1.0, "disabled", crop_path)

        best_score = 0.0
        best_label = None
        for label, template in self._templates:
            score = _best_match_score(crop, template)
            if score > best_score:
                best_score = score
                best_label = label

        return CursorValidationResult(
            matched=best_score >= CONFIG.cursor_validation_confidence,
            score=best_score,
            label=best_label,
            crop_path=crop_path,
        )

    def _capture_crop(self, screen_x: int, screen_y: int) -> np.ndarray:
        size = CONFIG.cursor_validation_crop_size
        half = size // 2
        monitor = {
            "left": max(0, int(screen_x - half)),
            "top": max(0, int(screen_y - half)),
            "width": size,
            "height": size,
        }
        image = np.array(self._capture_for_current_thread().grab(monitor))
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    def _capture_for_current_thread(self):
        thread_id = threading.get_ident()
        if self._sct is None or self._thread_id != thread_id:
            self._sct = mss.mss()
            self._thread_id = thread_id
        return self._sct


def _load_cursor_templates() -> list[tuple[str, np.ndarray]]:
    templates = []
    for path in sorted(CONFIG.cursor_templates_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in CONFIG.template_extensions:
            continue
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        if image.ndim == 3 and image.shape[2] == 4:
            alpha = image[:, :, 3]
            rgb = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB)
            image = cv2.cvtColor(_trim_transparent_border(rgb, alpha), cv2.COLOR_RGB2BGR)
        templates.append((path.stem, image))
    return templates


def _trim_transparent_border(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    rows, cols = np.where(alpha > 0)
    if len(rows) == 0 or len(cols) == 0:
        return rgb
    top, bottom = int(rows.min()), int(rows.max()) + 1
    left, right = int(cols.min()), int(cols.max()) + 1
    return rgb[top:bottom, left:right]


def _best_match_score(crop: np.ndarray, template: np.ndarray) -> float:
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    best_score = 0.0
    for scale in (0.80, 0.90, 1.00, 1.10, 1.20):
        width = max(4, int(template_gray.shape[1] * scale))
        height = max(4, int(template_gray.shape[0] * scale))
        if width > crop_gray.shape[1] or height > crop_gray.shape[0]:
            continue
        scaled = cv2.resize(template_gray, (width, height), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(crop_gray, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_value, _, _ = cv2.minMaxLoc(result)
        best_score = max(best_score, float(max_value))
    return best_score
