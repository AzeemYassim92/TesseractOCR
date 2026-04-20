import time

import pyautogui

from AutoTargeting.config import CONFIG
from AutoTargeting.tracker import TrackedTarget


class MouseAttacker:
    def __init__(self) -> None:
        self._last_click_at = 0.0
        pyautogui.PAUSE = 0

    def can_click(self) -> bool:
        return time.monotonic() - self._last_click_at >= CONFIG.attack_click_cooldown_seconds

    def right_click_target(self, target: TrackedTarget) -> tuple[int, int] | None:
        if not CONFIG.attack_enabled or not self.can_click():
            return None

        screen_x, screen_y = target_screen_center(target)
        pyautogui.click(x=screen_x, y=screen_y, button=CONFIG.attack_button)
        self._last_click_at = time.monotonic()
        return screen_x, screen_y


def target_screen_center(target: TrackedTarget) -> tuple[int, int]:
    region_left, region_top, _, _ = CONFIG.combat_region
    target_x, target_y = target.center
    return int(region_left + target_x), int(region_top + target_y)
