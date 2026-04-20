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

    def right_click_near_player(self) -> AttackResult:
        if not CONFIG.attack_enabled or not self.can_click():
            return AttackResult(False, None, 0, None, "cooldown_or_disabled")

        if CONFIG.cursor_validation_enabled and self.cursor_template_count == 0:
            return AttackResult(False, None, 0, None, "missing_cursor_templates")

        validation = None
        for screen_x, screen_y in player_screen_points():
            pyautogui.moveTo(screen_x, screen_y)
            time.sleep(CONFIG.cursor_hover_seconds)
            validation = self._cursor_validator.validate_at(screen_x, screen_y)
            if validation.matched:
                return self._click_validated_point(screen_x, screen_y, validation)

        return AttackResult(False, None, 0, validation, "player_cursor_not_found")

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
    padding = CONFIG.target_scan_padding_pixels
    points = [
        (target.x + target.width * 0.50, target.y + target.height * 0.62),
        (target.x + target.width * 0.50, target.y + target.height * 0.75),
        (target.x + target.width * 0.38, target.y + target.height * 0.68),
        (target.x + target.width * 0.62, target.y + target.height * 0.68),
        (target.x + target.width * 0.28, target.y + target.height * 0.78),
        (target.x + target.width * 0.72, target.y + target.height * 0.78),
        (target.x + target.width * 0.50, target.y + target.height + padding),
        (target.x + target.width * 0.38, target.y + target.height + padding),
        (target.x + target.width * 0.62, target.y + target.height + padding),
    ]

    unique_points = []
    seen = set()
    region_width = CONFIG.combat_region[2]
    region_height = CONFIG.combat_region[3]
    for x, y in points:
        bounded_x = int(max(0, min(region_width - 1, x)))
        bounded_y = int(max(0, min(region_height - 1, y)))
        screen_point = (int(region_left + bounded_x), int(region_top + bounded_y))
        if screen_point in seen:
            continue
        seen.add(screen_point)
        unique_points.append(screen_point)
    return unique_points


def player_screen_points() -> list[tuple[int, int]]:
    region_left, region_top, _, _ = CONFIG.combat_region
    if CONFIG.ignore_regions:
        x, y, width, height = CONFIG.ignore_regions[0]
        anchor_x = x + width / 2.0
        anchor_y = y + height * 0.78
    else:
        anchor_x = CONFIG.combat_region[2] / 2.0
        anchor_y = CONFIG.combat_region[3] * 0.60

    radius = CONFIG.player_cursor_scan_radius_pixels
    step = max(20, CONFIG.player_cursor_scan_step_pixels)
    offsets = [
        (0, 0),
        (0, step),
        (0, step * 2),
        (-step, 0),
        (step, 0),
        (-step, step),
        (step, step),
        (-step, step * 2),
        (step, step * 2),
        (-radius, step),
        (radius, step),
        (-radius, step * 2),
        (radius, step * 2),
    ]

    unique_points = []
    seen = set()
    region_width = CONFIG.combat_region[2]
    region_height = CONFIG.combat_region[3]
    for offset_x, offset_y in offsets:
        x = int(max(0, min(region_width - 1, anchor_x + offset_x)))
        y = int(max(0, min(region_height - 1, anchor_y + offset_y)))
        screen_point = (int(region_left + x), int(region_top + y))
        if screen_point in seen:
            continue
        seen.add(screen_point)
        unique_points.append(screen_point)
    return unique_points
