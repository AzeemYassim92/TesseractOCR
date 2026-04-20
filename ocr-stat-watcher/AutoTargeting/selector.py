import math
import time

from AutoTargeting.config import CONFIG
from AutoTargeting.tracker import TrackedTarget


def select_attack_target(targets: list[TrackedTarget]) -> TrackedTarget | None:
    eligible = [target for target in targets if _is_eligible(target)]
    if not eligible:
        return None

    anchor_x, anchor_y = _player_anchor()
    return min(
        eligible,
        key=lambda target: (
            0 if _is_near_moving_motion(target, anchor_x, anchor_y) else 1,
            0 if target.source == "color" else 1,
            0 if target.source == "template" else 1,
            _distance_from_anchor(target, anchor_x, anchor_y),
        ),
    )


def _is_eligible(target: TrackedTarget) -> bool:
    if target.dead or target.attacked:
        return False
    if target.seen_count < CONFIG.target_min_seen_count:
        return False
    anchor_x, anchor_y = _player_anchor()
    if _distance_from_anchor(target, anchor_x, anchor_y) > CONFIG.attack_threat_radius_pixels:
        return False
    if target.source in {"color", "template"} and CONFIG.template_targets_can_attack_idle:
        return True
    if target.status(time.monotonic()) != "moving":
        return False
    return True


def _player_anchor() -> tuple[float, float]:
    if not CONFIG.ignore_regions:
        width = CONFIG.combat_region[2]
        height = CONFIG.combat_region[3]
        return width / 2.0, height / 2.0

    x, y, width, height = CONFIG.ignore_regions[0]
    return x + width / 2.0, y + height / 2.0


def _distance_from_anchor(target: TrackedTarget, anchor_x: float, anchor_y: float) -> float:
    target_x, target_y = target.center
    return math.dist((target_x, target_y), (anchor_x, anchor_y))


def _is_near_moving_motion(target: TrackedTarget, anchor_x: float, anchor_y: float) -> bool:
    if target.source != "motion":
        return False
    if target.status(time.monotonic()) != "moving":
        return False
    return _distance_from_anchor(target, anchor_x, anchor_y) <= CONFIG.attack_threat_radius_pixels
