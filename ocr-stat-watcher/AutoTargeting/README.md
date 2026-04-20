# AutoTargeting Experiment

Standalone combat detection sandbox. This folder is intentionally isolated from the working OCR watcher so it can be deleted safely if the experiment does not work.

## Run

```powershell
cd C:\Repos\2026\tesseract\ocr-stat-watcher
.\.venv\Scripts\Activate.ps1
python -m AutoTargeting.runner
```

## Folders

- `images/`: put monster/object template images here.
- `cursor_templates/`: put attack-cursor PNGs here, for example `attack_cursor.png`.
- `debug/latest_raw.png`: latest captured combat region.
- `debug/latest_overlay.png`: latest capture with candidate boxes drawn.
- `debug/latest_cursor_crop.png`: latest small crop used for attack-cursor validation.

## Current Behavior

- Captures combat region `(6, 0, 1913, 1017)`.
- Runs template matching against images in `AutoTargeting/images`.
- Also runs simple motion/blob detection between frames.
- Filters attack candidates through a pink/red monster-color check to reduce grass/shadow lock-ons.
- Tracks moving candidates as target IDs so a monster can pause without immediately being forgotten.
- Draws thin candidate boxes plus thicker tracked target boxes.
- Draws configured ignore regions in gray. The first ignore region is the fixed player character area `(897, 396, 115, 183)`.
- Chooses a proposed next target with a blue `NEXT ATTACK` box.
- Only initiates motion-based attacks on currently moving targets, not remembered idle ground noise.
- Allows color/template-matched targets to be attacked while idle, since a stationary monster can still be valid.
- Ignores attack targets farther than the configured player threat radius.
- Prioritizes moving targets near the player over far-away template matches.
- Hovers candidate points and checks for an attack cursor before clicking.
- Right-clicks a validated point multiple times when attack mode is enabled.
- Waits for `attack_success_pause_seconds` after a validated attack burst before trying another attack.
- Green target boxes are moving, amber target boxes are remembered but currently idle, and gray is reserved for attacked targets that stopped moving.
- After a right-click, the target is marked as attacked so the same target ID is not clicked again.
- If the player character area does not show movement/attack animation shortly after a right-click, nearby targets around that clicked spot are rejected for a while.
- Does not mark random stationary monsters as dead. A target must be explicitly marked as attacked before the dead timer can apply.

## Notes

Set `attack_enabled` in `AutoTargeting/config.py` to switch between visual-only targeting and mouse attack mode.

Add your cursor PNGs to `AutoTargeting/cursor_templates`. The transparent/no-background cursor image is usually the better first template, but you can add both versions and the validator will try all PNG/JPG/BMP files in the folder.
