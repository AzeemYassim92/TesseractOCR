from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from AutoTargeting.config import CONFIG


@dataclass(frozen=True)
class Candidate:
    x: int
    y: int
    width: int
    height: int
    score: float
    source: str
    label: str


def load_templates() -> list[tuple[str, np.ndarray]]:
    CONFIG.images_dir.mkdir(parents=True, exist_ok=True)
    templates = []
    for path in sorted(CONFIG.images_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in CONFIG.template_extensions:
            continue
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        if image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        templates.append((path.stem, image))
    return templates


def detect_templates(frame: np.ndarray, templates: list[tuple[str, np.ndarray]]) -> list[Candidate]:
    candidates = []
    haystack = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    for label, template in templates:
        needle_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        for scale in CONFIG.template_scales:
            scaled = _resize_template(needle_gray, scale)
            if scaled is None:
                continue
            height, width = scaled.shape[:2]
            if height > haystack.shape[0] or width > haystack.shape[1]:
                continue

            result = cv2.matchTemplate(haystack, scaled, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= CONFIG.template_confidence)
            for y, x in zip(*locations):
                score = float(result[y, x])
                candidates.append(
                    Candidate(
                        x=int(x),
                        y=int(y),
                        width=int(width),
                        height=int(height),
                        score=score,
                        source="template",
                        label=label,
                    )
                )
    return _dedupe_candidates(candidates)


def detect_motion(frame: np.ndarray, previous_frame: np.ndarray | None) -> list[Candidate]:
    if previous_frame is None or not CONFIG.motion_enabled:
        return []

    current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    previous_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
    delta = cv2.absdiff(current_gray, previous_gray)
    blurred = cv2.GaussianBlur(delta, (5, 5), 0)
    _, mask = cv2.threshold(blurred, CONFIG.motion_threshold, 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < CONFIG.motion_min_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        candidates.append(
            Candidate(
                x=int(x),
                y=int(y),
                width=int(width),
                height=int(height),
                score=float(area),
                source="motion",
                label="motion",
            )
        )
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return candidates[: CONFIG.max_candidates]


def detect_monster_color(frame: np.ndarray) -> list[Candidate]:
    if not CONFIG.monster_color_enabled:
        return []

    mask = _monster_color_mask(frame)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < CONFIG.monster_color_min_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        candidate = Candidate(
            x=int(x),
            y=int(y),
            width=int(width),
            height=int(height),
            score=float(area),
            source="color",
            label="monster",
        )
        if _is_ignored(candidate):
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return _dedupe_candidates(candidates)


def detect_candidates(
    frame: np.ndarray,
    previous_frame: np.ndarray | None,
    templates: list[tuple[str, np.ndarray]],
) -> list[Candidate]:
    color_candidates = detect_monster_color(frame)
    template_candidates = [
        candidate
        for candidate in detect_templates(frame, templates)
        if _has_monster_color(frame, candidate)
    ]
    motion_candidates = [
        candidate
        for candidate in detect_motion(frame, previous_frame)
        if _has_monster_color(frame, candidate)
    ]

    candidates = color_candidates
    candidates.extend(template_candidates)
    candidates.extend(motion_candidates)
    candidates = [candidate for candidate in candidates if not _is_ignored(candidate)]
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return _dedupe_candidates(candidates)[: CONFIG.max_candidates]


def _resize_template(template: np.ndarray, scale: float) -> np.ndarray | None:
    if scale <= 0:
        return None
    width = max(1, int(template.shape[1] * scale))
    height = max(1, int(template.shape[0] * scale))
    if width < 4 or height < 4:
        return None
    return cv2.resize(template, (width, height), interpolation=cv2.INTER_AREA)


def _dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    kept = []
    for candidate in candidates:
        if any(_overlap_ratio(candidate, existing) > 0.45 for existing in kept):
            continue
        kept.append(candidate)
        if len(kept) >= CONFIG.max_candidates:
            break
    return kept


def _overlap_ratio(a: Candidate, b: Candidate) -> float:
    ax2 = a.x + a.width
    ay2 = a.y + a.height
    bx2 = b.x + b.width
    by2 = b.y + b.height

    overlap_x = max(0, min(ax2, bx2) - max(a.x, b.x))
    overlap_y = max(0, min(ay2, by2) - max(a.y, b.y))
    overlap_area = overlap_x * overlap_y
    if overlap_area == 0:
        return 0.0

    smaller_area = min(a.width * a.height, b.width * b.height)
    return overlap_area / float(max(1, smaller_area))


def _is_ignored(candidate: Candidate) -> bool:
    center_x = candidate.x + candidate.width / 2.0
    center_y = candidate.y + candidate.height / 2.0
    for region in CONFIG.ignore_regions:
        if _point_inside_region(center_x, center_y, region):
            return True
    return False


def _point_inside_region(x: float, y: float, region: tuple[int, int, int, int]) -> bool:
    region_x, region_y, width, height = region
    return region_x <= x <= region_x + width and region_y <= y <= region_y + height


def _has_monster_color(frame: np.ndarray, candidate: Candidate) -> bool:
    if not CONFIG.monster_color_enabled:
        return True

    padding = CONFIG.monster_color_candidate_padding
    x1 = max(0, candidate.x - padding)
    y1 = max(0, candidate.y - padding)
    x2 = min(frame.shape[1], candidate.x + candidate.width + padding)
    y2 = min(frame.shape[0], candidate.y + candidate.height + padding)
    if x2 <= x1 or y2 <= y1:
        return False

    mask = _monster_color_mask(frame[y1:y2, x1:x2])
    return cv2.countNonZero(mask) >= CONFIG.monster_color_min_pixels_in_candidate


def _monster_color_mask(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red = cv2.inRange(hsv, np.array((0, 70, 45)), np.array((14, 255, 255)))
    upper_red = cv2.inRange(hsv, np.array((165, 70, 45)), np.array((179, 255, 255)))
    magenta = cv2.inRange(hsv, np.array((135, 55, 45)), np.array((179, 255, 255)))
    return cv2.bitwise_or(cv2.bitwise_or(lower_red, upper_red), magenta)
