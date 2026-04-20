import time

from AutoTargeting.config import CONFIG
from AutoTargeting.controller import AutoTargetingController


def main() -> None:
    CONFIG.images_dir.mkdir(parents=True, exist_ok=True)
    CONFIG.debug_dir.mkdir(parents=True, exist_ok=True)

    controller = AutoTargetingController()

    mode = "attack mode" if CONFIG.attack_enabled else "observe mode"
    print(f"AutoTargeting {mode}. Press Ctrl+C to stop.")
    print(f"Combat region: {CONFIG.combat_region}")
    print(f"Template folder: {CONFIG.images_dir}")
    print(f"Cursor template folder: {CONFIG.cursor_templates_dir}")
    print(f"Loaded templates: {controller.template_count}")
    print(f"Loaded cursor templates: {controller.cursor_template_count}")
    print(f"Debug overlay: {CONFIG.debug_dir / 'latest_overlay.png'}")

    try:
        while True:
            controller.tick()
            time.sleep(CONFIG.loop_interval_seconds)
    except KeyboardInterrupt:
        print("\nAutoTargeting stopped.")


if __name__ == "__main__":
    main()
