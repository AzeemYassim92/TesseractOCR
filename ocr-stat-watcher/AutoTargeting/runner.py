import time

from AutoTargeting.attacker import MouseAttacker
from AutoTargeting.capture import RegionCapture
from AutoTargeting.config import CONFIG
from AutoTargeting.debug import save_debug_images
from AutoTargeting.detector import detect_candidates, load_templates
from AutoTargeting.player_activity import has_player_activity
from AutoTargeting.selector import select_attack_target
from AutoTargeting.tracker import TargetTracker


def main() -> None:
    CONFIG.images_dir.mkdir(parents=True, exist_ok=True)
    CONFIG.debug_dir.mkdir(parents=True, exist_ok=True)

    capture = RegionCapture()
    templates = load_templates()
    tracker = TargetTracker()
    attacker = MouseAttacker()
    previous_frame = None
    pending_attack_target_id = None
    pending_attack_started_at = 0.0
    pending_player_activity = False

    mode = "attack mode" if CONFIG.attack_enabled else "observe mode"
    print(f"AutoTargeting {mode}. Press Ctrl+C to stop.")
    print(f"Combat region: {CONFIG.combat_region}")
    print(f"Template folder: {CONFIG.images_dir}")
    print(f"Cursor template folder: {CONFIG.cursor_templates_dir}")
    print(f"Loaded templates: {len(templates)}")
    print(f"Loaded cursor templates: {attacker.cursor_template_count}")
    print(f"Debug overlay: {CONFIG.debug_dir / 'latest_overlay.png'}")

    try:
        while True:
            now = time.monotonic()
            frame = capture.grab(CONFIG.combat_region)
            player_active = has_player_activity(frame, previous_frame)
            candidates = detect_candidates(frame, previous_frame, templates)
            targets = tracker.update(candidates)

            if pending_attack_target_id is not None:
                pending_player_activity = pending_player_activity or player_active
                if pending_player_activity:
                    print(f"CONFIRMED: player reacted to target#{pending_attack_target_id}")
                    pending_attack_target_id = None
                    pending_player_activity = False
                elif now - pending_attack_started_at >= CONFIG.attack_confirm_window_seconds:
                    print(
                        f"REJECTED: target#{pending_attack_target_id} "
                        "did not trigger player movement/attack"
                    )
                    tracker.reject_target(pending_attack_target_id)
                    pending_attack_target_id = None
                    pending_player_activity = False
                    targets = tracker.active_targets()

            selected_target = select_attack_target(targets)
            clicked_at = None
            if selected_target is not None and pending_attack_target_id is None:
                attack_result = attacker.right_click_target(selected_target)
                clicked_at = attack_result.screen_position
                if attack_result.clicked and clicked_at is not None:
                    tracker.mark_attacked(selected_target.id)
                    pending_attack_target_id = selected_target.id
                    pending_attack_started_at = now
                    pending_player_activity = False
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
                    tracker.reject_target(selected_target.id)
                    validation = attack_result.cursor_validation
                    print(
                        f"REJECTED: target#{selected_target.id} did not show attack cursor "
                        f"score={validation.score if validation else 0:.2f} "
                        f"crop={validation.crop_path if validation else None}"
                    )
            save_debug_images(frame, candidates, targets, selected_target)

            summary = ", ".join(
                f"{candidate.source}:{candidate.label}@({candidate.x},{candidate.y})={candidate.score:.2f}"
                for candidate in candidates[:5]
            )
            target_summary = ", ".join(
                f"#{target.id}:{target.status(time.monotonic())}@({target.x},{target.y})"
                for target in targets[:5]
            )
            attack_summary = (
                f"attacked=#{selected_target.id}@screen{clicked_at}"
                if clicked_at is not None and selected_target is not None
                else f"next_attack=#{selected_target.id}@({selected_target.x},{selected_target.y})"
                if selected_target is not None
                else "next_attack=None"
            )
            print(
                f"AutoTargeting candidates={len(candidates)} "
                f"targets={len(targets)} {attack_summary} {summary} | {target_summary}"
            )

            previous_frame = frame
            time.sleep(CONFIG.loop_interval_seconds)
    except KeyboardInterrupt:
        print("\nAutoTargeting stopped.")


if __name__ == "__main__":
    main()
