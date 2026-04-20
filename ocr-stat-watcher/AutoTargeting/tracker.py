from __future__ import annotations

from dataclasses import dataclass
import math
import time

from AutoTargeting.config import CONFIG
from AutoTargeting.detector import Candidate


@dataclass
class TrackedTarget:
    id: int
    x: int
    y: int
    width: int
    height: int
    score: float
    source: str
    label: str
    first_seen: float
    last_seen: float
    last_motion_seen: float
    seen_count: int = 1
    attacked: bool = False
    dead: bool = False

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    def status(self, now: float) -> str:
        if self.dead:
            return "dead"
        if now - self.last_motion_seen <= CONFIG.loop_interval_seconds * 2.5:
            return "moving"
        return "idle"


class TargetTracker:
    def __init__(self) -> None:
        self._targets: dict[int, TrackedTarget] = {}
        self._rejected_points: list[tuple[float, float, float]] = []
        self._next_id = 1

    def update(self, candidates: list[Candidate], now: float | None = None) -> list[TrackedTarget]:
        now = time.monotonic() if now is None else now
        self._expire_rejected_points(now)
        matched_target_ids: set[int] = set()

        for candidate in candidates:
            if self._is_rejected_candidate(candidate, now):
                continue
            target = self._find_best_target(candidate, matched_target_ids)
            if target is None:
                target = self._create_target(candidate, now)
            else:
                self._refresh_target(target, candidate, now)
            matched_target_ids.add(target.id)

        self._expire_targets(now)
        return sorted(self._targets.values(), key=lambda target: (target.dead, -target.last_seen, target.id))

    def mark_attacked(self, target_id: int) -> None:
        target = self._targets.get(target_id)
        if target is not None:
            target.attacked = True

    def reject_target(self, target_id: int) -> None:
        target = self._targets.pop(target_id, None)
        if target is None:
            return
        center_x, center_y = target.center
        expires_at = time.monotonic() + CONFIG.rejected_target_cooldown_seconds
        self._rejected_points.append((center_x, center_y, expires_at))
        self._remove_targets_near(center_x, center_y)

    def active_targets(self) -> list[TrackedTarget]:
        return [target for target in self._targets.values() if not target.dead]

    def _create_target(self, candidate: Candidate, now: float) -> TrackedTarget:
        target = TrackedTarget(
            id=self._next_id,
            x=candidate.x,
            y=candidate.y,
            width=candidate.width,
            height=candidate.height,
            score=candidate.score,
            source=candidate.source,
            label=candidate.label,
            first_seen=now,
            last_seen=now,
            last_motion_seen=now if candidate.source == "motion" else 0.0,
        )
        self._next_id += 1
        self._targets[target.id] = target
        return target

    def _refresh_target(self, target: TrackedTarget, candidate: Candidate, now: float) -> None:
        target.x = candidate.x
        target.y = candidate.y
        target.width = candidate.width
        target.height = candidate.height
        target.score = candidate.score
        target.source = candidate.source
        target.label = candidate.label
        target.last_seen = now
        target.seen_count += 1
        target.dead = False
        if candidate.source == "motion":
            target.last_motion_seen = now

    def _expire_targets(self, now: float) -> None:
        expired_ids = []
        for target_id, target in self._targets.items():
            idle_seconds = now - target.last_motion_seen
            unseen_seconds = now - target.last_seen

            if target.attacked and not target.dead and idle_seconds >= CONFIG.attacked_dead_after_seconds:
                target.dead = True

            if target.dead and unseen_seconds >= CONFIG.dead_keepalive_seconds:
                expired_ids.append(target_id)
            elif not target.attacked and unseen_seconds >= CONFIG.unattacked_keepalive_seconds:
                expired_ids.append(target_id)

        for target_id in expired_ids:
            self._targets.pop(target_id, None)

    def _expire_rejected_points(self, now: float) -> None:
        self._rejected_points = [
            point for point in self._rejected_points if point[2] > now
        ]

    def _is_rejected_candidate(self, candidate: Candidate, now: float) -> bool:
        candidate_center = (candidate.x + candidate.width / 2.0, candidate.y + candidate.height / 2.0)
        for rejected_x, rejected_y, expires_at in self._rejected_points:
            if expires_at <= now:
                continue
            if math.dist(candidate_center, (rejected_x, rejected_y)) <= CONFIG.rejected_target_radius_pixels:
                return True
        return False

    def _remove_targets_near(self, x: float, y: float) -> None:
        target_ids = [
            target.id
            for target in self._targets.values()
            if math.dist(target.center, (x, y)) <= CONFIG.rejected_target_radius_pixels
        ]
        for target_id in target_ids:
            self._targets.pop(target_id, None)

    def _find_best_target(
        self,
        candidate: Candidate,
        already_matched: set[int],
    ) -> TrackedTarget | None:
        best_target = None
        best_score = float("-inf")

        for target in self._targets.values():
            if target.id in already_matched or target.dead:
                continue

            distance = _center_distance(candidate, target)
            iou = _iou(candidate, target)
            if distance > CONFIG.target_match_distance_pixels and iou < CONFIG.target_match_iou:
                continue

            score = iou * 100.0 - distance
            if score > best_score:
                best_score = score
                best_target = target

        return best_target


def _center_distance(candidate: Candidate, target: TrackedTarget) -> float:
    candidate_center = (candidate.x + candidate.width / 2.0, candidate.y + candidate.height / 2.0)
    target_center = target.center
    return math.dist(candidate_center, target_center)


def _iou(candidate: Candidate, target: TrackedTarget) -> float:
    ax2 = candidate.x + candidate.width
    ay2 = candidate.y + candidate.height
    bx2 = target.x + target.width
    by2 = target.y + target.height

    overlap_x = max(0, min(ax2, bx2) - max(candidate.x, target.x))
    overlap_y = max(0, min(ay2, by2) - max(candidate.y, target.y))
    overlap_area = overlap_x * overlap_y
    if overlap_area == 0:
        return 0.0

    candidate_area = candidate.width * candidate.height
    target_area = target.width * target.height
    union_area = candidate_area + target_area - overlap_area
    return overlap_area / float(max(1, union_area))
