from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Thresholds:
    hp_trigger_at_or_below: int = 650
    hp_reset_above: int = 750
    mp_trigger_at_or_below: int = 300
    mp_reset_above: int = 450


@dataclass(frozen=True)
class PotionConfig:
    hp_potion_name: str = "p2"
    hp_potion_heal_amount: int = 240
    hp_burst_max_presses: int = 4


@dataclass(frozen=True)
class Timings:
    poll_interval_seconds: float = 0.10
    action_cooldown_seconds: float = 1.00
    hp_action_cooldown_seconds: float = 0.20
    mp_action_cooldown_seconds: float = 0.20
    stable_reads_required: int = 1
    key_hold_seconds: float = 0.05
    suspicious_low_confirmation_reads: int = 2
    hp_suspicious_low_confirmation_reads: int = 1
    mp_suspicious_low_confirmation_reads: int = 1
    suspicious_low_ratio: float = 0.20
    suspicious_low_min_delta: int = 35
    max_value_jump_ratio: float = 1.5
    max_change_confirmation_reads: int = 1


@dataclass(frozen=True)
class OCRConfig:
    tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    tesseract_psm: int = 7
    whitelist: str = "0123456789/"
    upscale_factor: int = 4
    threshold_value: int = 130
    hp_upscale_factor: int = 4
    hp_threshold_value: int = 130
    mp_upscale_factor: int = 5
    mp_threshold_value: int = 136


@dataclass(frozen=True)
class CaptureConfig:
    prefer_dxcam: bool = True


@dataclass(frozen=True)
class WarehouseConfig:
    enabled: bool = True
    run_all_hotkey: str = "e"
    stop_hotkey: str = "l"
    clicks_per_slot: int = 2
    click_interval_seconds: float = 0.03
    slot_interval_seconds: float = 0.05
    run_start_delay_seconds: float = 0.20
    points: tuple[tuple[int, int], ...] = (
        (1631, 132),
        (1682, 124),
        (1727, 127),
        (1773, 128),
        (1817, 128),
        (1877, 129),
        (1633, 177),
        (1676, 173),
        (1725, 174),
        (1778, 173),
        (1821, 174),
        (1866, 174),
        (1635, 216),
        (1678, 218),
        (1723, 219),
        (1773, 219),
        (1821, 222),
        (1862, 218),
        (1633, 265),
        (1680, 267),
        (1724, 266),
        (1769, 267),
        (1820, 266),
        (1866, 264),
        (1631, 314),
        (1676, 314),
        (1728, 311),
        (1771, 316),
        (1820, 313),
        (1867, 315),
        (1637, 361),
        (1682, 358),
        (1728, 362),
        (1768, 357),
        (1814, 356),
        (1856, 359),
        (1639, 406),
        (1678, 406),
        (1725, 405),
        (1776, 409),
        (1817, 406),
        (1870, 409),
        (1633, 452),
        (1676, 450),
        (1724, 452),
        (1774, 448),
        (1816, 453),
        (1858, 450),
        (1645, 494),
        (1683, 496),
        (1727, 496),
        (1775, 498),
        (1818, 496),
        (1860, 501),
        (1632, 543),
        (1681, 544),
        (1732, 543),
        (1772, 542),
        (1822, 542),
        (1862, 541),
    )


@dataclass(frozen=True)
class LootConfig:
    enabled: bool = True
    toggle_hotkey: str = "q"
    key: str = "space"
    interval_seconds: float = 0.25


@dataclass(frozen=True)
class ActionKeys:
    hp_key: str = "z"
    mp_key: str = "x"


@dataclass(frozen=True)
class HotkeyConfig:
    auto_targeting_toggle_hotkey: str = "w"
    ocr_actions_toggle_hotkey: str = "r"
    profile_status_hotkey: str = "t"


@dataclass(frozen=True)
class ProfileConfig:
    profiles_dir: Path = ROOT_DIR / "profiles"
    default_profile: str = "main"


THRESHOLDS = Thresholds()
POTIONS = PotionConfig()
TIMINGS = Timings()
OCR = OCRConfig()
KEYS = ActionKeys()
CAPTURE = CaptureConfig()
WAREHOUSE = WarehouseConfig()
LOOT = LootConfig()
HOTKEYS = HotkeyConfig()
PROFILES = ProfileConfig()
