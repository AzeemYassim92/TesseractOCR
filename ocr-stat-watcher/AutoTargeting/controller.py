import threading
import time

from AutoTargeting.attacker import MouseAttacker
from AutoTargeting.capture import RegionCapture
from AutoTargeting.config import CONFIG
from AutoTargeting.debug import save_debug_images
from AutoTargeting.detector import detect_candidates, load_templates
from AutoTargeting.player_activity import has_player_activity
from AutoTargeting.selector import select_attack_target
from AutoTargeting.tracker import TargetTracker


class AutoTargetingController:
    def __init__(self) -> None:
        CONFIG.images_dir.mkdir(parents=True, exist_ok=True)
        CONFIG.debug_dir.mkdir(parents=True, exist_ok=True)
        CONFIG.cursor_templates_dir.mkdir(parents=True, exist_ok=True)

        self._capture = RegionCapture()
        self._templates = load_templates()
        self._tracker = TargetTracker()
        self._attacker = MouseAttacker()
        self._previous_frame = None
        self._pending_attack_target_id = None
        self._pending_attack_started_at = 0.0
        self._pending_player_activity = False
        self._enabled = False
        self._thread = None
        self._stop_requested = threading.Event()
        self._lock = threading.Lock()

    @property
    def template_count(self) -> int:
        return len(self._templates)

    @property
    def cursor_template_count(self) -> int:
        return self._attacker.cursor_template_count

    def start(self) -> None:
        with self._lock:
            if self._enabled:
                print("AUTOTARGET: already ON")
                return
            self._enabled = True
            self._stop_requested.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        print("AUTOTARGET: ON")

    def stop(self) -> None:
        with self._lock:
            if not self._enabled:
                return
            self._enabled = False
            self._stop_requested.set()
        print("AUTOTARGET: OFF")

    def toggle(self) -> None:
        if self.is_enabled():
            self.stop()
        else:
            self.start()

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def shutdown(self) -> None:
        self.stop()

    def _run_loop(self) -> None:
        while not self._stop_requested.is_set():
            self.tick()
            self._stop_requested.wait(max(0.01, CONFIG.loop_interval_seconds))

    def tick(self) -> None:
        now = time.monotonic()
        frame = self._capture.grab(CONFIG.combat_region)
        player_active = has_player_activity(frame, self._previous_frame)
        candidates = detect_candidates(frame, self._previous_frame, self._templates)
        targets = self._tracker.update(candidates)

        if self._pending_attack_target_id is not None:
            self._pending_player_activity = self._pending_player_activity or player_active
            if self._pending_player_activity:
                print(f"CONFIRMED: player reacted to target#{self._pending_attack_target_id}")
                self._pending_attack_target_id = None
                self._pending_player_activity = False
            elif now - self._pending_attack_started_at >= CONFIG.attack_confirm_window_seconds:
                print(
                    f"REJECTED: target#{self._pending_attack_target_id} "
                    "did not trigger player movement/attack"
                )
                self._tracker.reject_target(self._pending_attack_target_id)
                self._pending_attack_target_id = None
                self._pending_player_activity = False
                targets = self._tracker.active_targets()

        selected_target = select_attack_target(targets)
        clicked_at = None
        if selected_target is not None and self._pending_attack_target_id is None:
            attack_result = self._attacker.right_click_target(selected_target)
            clicked_at = attack_result.screen_position
            if attack_result.clicked and clicked_at is not None:
                self._tracker.mark_attacked(selected_target.id)
                self._pending_attack_target_id = selected_target.id
                self._pending_attack_started_at = now
                self._pending_player_activity = False
                print(
                    f"ATTACK: right-clicked target#{selected_target.id} "
                    f"{attack_result.clicks_sent}x at screen={clicked_at} "
                    f"cursor={attack_result.cursor_validation.label if attack_result.cursor_validation else None} "
                    f"score={attack_result.cursor_validation.score if attack_result.cursor_validation else 0:.2f}"
                )
            elif attack_result.reason == "missing_cursor_templates":
                print(
                    "SKIP: cursor validation is enabled, but no cursor templates were found in "
                    f"{CONFIG.cursor_templates_dir}"
                )
            elif attack_result.reason == "cursor_not_validated":
                self._tracker.reject_target(selected_target.id)
                validation = attack_result.cursor_validation
                print(
                    f"REJECTED: target#{selected_target.id} did not show attack cursor "
                    f"score={validation.score if validation else 0:.2f} "
                    f"crop={validation.crop_path if validation else None}"
                )

        save_debug_images(frame, candidates, targets, selected_target)
        self._previous_frame = frame
