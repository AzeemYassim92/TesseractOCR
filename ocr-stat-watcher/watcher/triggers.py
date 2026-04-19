import time
import keyboard
from config import THRESHOLDS, TIMINGS


class TriggerController:
    def __init__(self) -> None:
        self._last_action_time = 0.0

    def _can_fire(self) -> bool:
        return (time.time() - self._last_action_time) >= TIMINGS.action_cooldown_seconds

    def _fire(self, reason: str) -> None:
        if not self._can_fire():
            return
        keyboard.press_and_release("z")
        self._last_action_time = time.time()
        print(f"ACTION: pressed z because {reason}")

    def evaluate(self, hp_current: int, mp_current: int) -> None:
        if hp_current <= THRESHOLDS.hp_trigger_at_or_below:
            self._fire(f"hp <= {THRESHOLDS.hp_trigger_at_or_below} (hp={hp_current})")
            return

        if THRESHOLDS.mp_trigger_min <= mp_current <= THRESHOLDS.mp_trigger_max:
            self._fire(
                f"mp in range {THRESHOLDS.mp_trigger_min}-{THRESHOLDS.mp_trigger_max} (mp={mp_current})"
            )
