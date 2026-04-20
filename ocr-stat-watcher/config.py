from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:
    hp_trigger_at_or_below: int = 550
    hp_reset_above: int = 650
    mp_trigger_at_or_below: int = 200
    mp_reset_above: int = 350


@dataclass(frozen=True)
class Timings:
    poll_interval_seconds: float = 0.10
    action_cooldown_seconds: float = 1.00
    stable_reads_required: int = 1
    key_hold_seconds: float = 0.05


@dataclass(frozen=True)
class OCRConfig:
    tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    tesseract_psm: int = 7
    whitelist: str = "0123456789/"
    upscale_factor: int = 4
    threshold_value: int = 130


@dataclass(frozen=True)
class CaptureConfig:
    prefer_dxcam: bool = True


@dataclass(frozen=True)
class ActionKeys:
    hp_key: str = "z"
    mp_key: str = "x"


THRESHOLDS = Thresholds()
TIMINGS = Timings()
OCR = OCRConfig()
KEYS = ActionKeys()
CAPTURE = CaptureConfig()
