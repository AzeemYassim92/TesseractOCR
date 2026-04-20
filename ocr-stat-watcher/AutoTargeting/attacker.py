from dataclasses import dataclass
import time

import pyautogui

from AutoTargeting.config import CONFIG
from AutoTargeting.cursor_validator import CursorValidationResult, CursorValidator
from AutoTargeting.tracker import TrackedTarget


@dataclass(frozen=True)
class AttackResult:
    clicked: bool
    screen_position: tuple[int, int] | None
    clicks_sent: int
    cursor_validation: CursorValidationResult | None
    reason: str


class MouseAttacker:
    def __init__(self) -> None:
        self._last_click_at = 0.0
        self._cooldown_until = 0.0
        self._cursor_validator = CursorValidator()
        pyautogui.PAUSE = 0

    def can_click(self) -> bool:
        now = time.monotonic()
        return (
            now >= self._cooldown_until
            and now - self._last_click_at >= CONFIG.attack_click_cooldown_seconds
        )

    @property
    def cursor_template_count(self) -> int:
        return self._cursor_validator.template_count

    def right_click_target(self, target: TrackedTarget) -> AttackResult:
        if not CONFIG.attack_enabled or not self.can_click():
            return AttackResult(False, None, 0, None, "cooldown_or_disabled")

        if CONFIG.cursor_validation_enabled and self.cursor_template_count == 0:
            return AttackResult(False, None, 0, None, "missing_cursor_templates")

        validation = None
        for screen_x, screen_y in target_screen_points(target):
            pyautogui.moveTo(screen_x, screen_y)
            time.sleep(CONFIG.cursor_hover_seconds)
            validation = self._cursor_validator.validate_at(screen_x, screen_y)
            if validation.matched:
                return self._click_validated_point(screen_x, screen_y, validation)

        self._last_click_at = time.monotonic()
        return AttackResult(False, None, 0, validation, "cursor_not_validated")

    def _click_validated_point(
        self,
        screen_x: int,
        screen_y: int,
        validation: CursorValidationResult,
    ) -> AttackResult:
        clicks_sent = max(1, CONFIG.attack_repeat_clicks)
        for click_index in range(clicks_sent):
            pyautogui.click(x=screen_x, y=screen_y, button=CONFIG.attack_button)
            if click_index < clicks_sent - 1:
                time.sleep(CONFIG.attack_repeat_interval_seconds)
        self._last_click_at = time.monotonic()
        self._cooldown_until = self._last_click_at + CONFIG.attack_success_pause_seconds
        return AttackResult(True, (screen_x, screen_y), clicks_sent, validation, "clicked")


def target_screen_center(target: TrackedTarget) -> tuple[int, int]:
    region_left, region_top, _, _ = CONFIG.combat_region
    target_x, target_y = target.center
    return int(region_left + target_x), int(region_top + target_y)


def target_screen_points(target: TrackedTarget) -> list[tuple[int, int]]:
    region_left, region_top, _, _ = CONFIG.combat_region
    points = [
        target.center,
        (target.x + target.width * 0.50, target.y + target.height * 0.35),
        (target.x + target.width * 0.50, target.y + target.height * 0.65),
        (target.x + target.width * 0.35, target.y + target.height * 0.50),
        (target.x + target.width * 0.65, target.y + target.height * 0.50),
    ]

    unique_points = []
    seen = set()
    for x, y in points:
        screen_point = (int(region_left + x), int(region_top + y))
        if screen_point in seen:
            continue
        seen.add(screen_point)
        unique_points.append(screen_point)
    return unique_points
