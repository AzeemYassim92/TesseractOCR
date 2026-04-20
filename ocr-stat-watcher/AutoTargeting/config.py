from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class AutoTargetingConfig:
    # left, top, width, height
    combat_region: tuple[int, int, int, int] = (6, 0, 1913, 1017)
    # Regions are relative to the captured combat frame: x, y, width, height.
    ignore_regions: tuple[tuple[int, int, int, int], ...] = ((897, 396, 115, 183),)
    images_dir: Path = ROOT_DIR / "images"
    cursor_templates_dir: Path = ROOT_DIR / "cursor_templates"
    debug_dir: Path = ROOT_DIR / "debug"
    template_extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp")
    template_confidence: float = 0.72
    template_scales: tuple[float, ...] = (0.85, 0.95, 1.0, 1.05, 1.15)
    motion_enabled: bool = True
    motion_threshold: int = 28
    motion_min_area: int = 80
    monster_color_enabled: bool = True
    monster_color_min_area: int = 45
    monster_color_min_pixels_in_candidate: int = 18
    monster_color_candidate_padding: int = 10
    max_candidates: int = 25
    target_match_distance_pixels: int = 90
    target_match_iou: float = 0.12
    unattacked_keepalive_seconds: float = 8.0
    attacked_dead_after_seconds: float = 1.5
    dead_keepalive_seconds: float = 2.0
    target_min_seen_count: int = 2
    attack_threat_radius_pixels: int = 650
    template_targets_can_attack_idle: bool = True
    attack_enabled: bool = True
    attack_button: str = "right"
    attack_click_cooldown_seconds: float = 1.00
    attack_repeat_clicks: int = 4
    attack_repeat_interval_seconds: float = 0.55
    attack_success_pause_seconds: float = 3.5
    attack_confirm_window_seconds: float = 1.0
    cursor_validation_enabled: bool = True
    cursor_validation_confidence: float = 0.62
    cursor_validation_crop_size: int = 72
    cursor_hover_seconds: float = 0.08
    player_activity_threshold: int = 18
    player_activity_min_pixels: int = 80
    rejected_target_cooldown_seconds: float = 20.0
    rejected_target_radius_pixels: int = 120
    loop_interval_seconds: float = 0.25
    save_every_frame: bool = True


CONFIG = AutoTargetingConfig()
