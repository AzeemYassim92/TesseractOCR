import time

import cv2
import numpy as np

from AutoTargeting.config import CONFIG
from AutoTargeting.detector import Candidate
from AutoTargeting.tracker import TrackedTarget


def save_debug_images(
    frame: np.ndarray,
    candidates: list[Candidate],
    targets: list[TrackedTarget] | None = None,
    selected_target: TrackedTarget | None = None,
) -> None:
    CONFIG.debug_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(CONFIG.debug_dir / "latest_raw.png"), frame)
    cv2.imwrite(
        str(CONFIG.debug_dir / "latest_overlay.png"),
        draw_overlay(frame, candidates, targets or [], selected_target),
    )


def draw_overlay(
    frame: np.ndarray,
    candidates: list[Candidate],
    targets: list[TrackedTarget],
    selected_target: TrackedTarget | None,
) -> np.ndarray:
    overlay = frame.copy()
    _draw_ignore_regions(overlay)
    for candidate in candidates:
        color = (0, 255, 255) if candidate.source == "template" else (0, 128, 255)
        top_left = (candidate.x, candidate.y)
        bottom_right = (candidate.x + candidate.width, candidate.y + candidate.height)
        cv2.rectangle(overlay, top_left, bottom_right, color, 1)

        label = f"{candidate.source}:{candidate.label} {candidate.score:.2f}"
        text_origin = (candidate.x, max(12, candidate.y - 5))
        cv2.putText(
            overlay,
            label,
            text_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )

    now_label_time = time.monotonic()
    for target in targets:
        status = target.status(now_label_time)
        if status == "dead":
            color = (120, 120, 120)
        elif status == "idle":
            color = (255, 180, 0)
        else:
            color = (0, 255, 0)

        top_left = (target.x, target.y)
        bottom_right = (target.x + target.width, target.y + target.height)
        cv2.rectangle(overlay, top_left, bottom_right, color, 2)

        attacked = " attacked" if target.attacked else ""
        label = f"target#{target.id} {status}{attacked}"
        text_origin = (target.x, min(overlay.shape[0] - 6, target.y + target.height + 14))
        cv2.putText(
            overlay,
            label,
            text_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    if selected_target is not None:
        top_left = (selected_target.x, selected_target.y)
        bottom_right = (
            selected_target.x + selected_target.width,
            selected_target.y + selected_target.height,
        )
        cv2.rectangle(overlay, top_left, bottom_right, (255, 0, 0), 3)
        cv2.putText(
            overlay,
            f"NEXT ATTACK target#{selected_target.id}",
            (selected_target.x, max(18, selected_target.y - 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 0, 0),
            2,
            cv2.LINE_AA,
        )
    return overlay


def _draw_ignore_regions(overlay: np.ndarray) -> None:
    for index, region in enumerate(CONFIG.ignore_regions, start=1):
        x, y, width, height = region
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (180, 180, 180), 2)
        cv2.putText(
            overlay,
            f"ignore#{index}",
            (x, max(14, y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )
