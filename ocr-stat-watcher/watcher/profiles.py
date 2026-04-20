import argparse
import json
from dataclasses import asdict
from pathlib import Path

from config import PROFILES, THRESHOLDS, Thresholds


def build_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OCR stat watcher")
    parser.add_argument(
        "--profile",
        default=PROFILES.default_profile,
        help="Character profile name from the profiles folder.",
    )
    parser.add_argument(
        "--main",
        action="store_const",
        const="main",
        dest="profile",
        help="Use the main character profile.",
    )
    parser.add_argument(
        "--gins",
        action="store_const",
        const="gins",
        dest="profile",
        help="Use the Gins character profile.",
    )
    return parser


def ensure_default_profiles() -> None:
    PROFILES.profiles_dir.mkdir(parents=True, exist_ok=True)
    _write_profile_if_missing("main", THRESHOLDS)
    _write_profile_if_missing(
        "gins",
        Thresholds(
            hp_trigger_at_or_below=180,
            hp_reset_above=260,
            mp_trigger_at_or_below=80,
            mp_reset_above=140,
        ),
    )


def load_profile(profile_name: str) -> tuple[str, Thresholds]:
    ensure_default_profiles()
    safe_name = _safe_profile_name(profile_name)
    profile_path = PROFILES.profiles_dir / f"{safe_name}.json"
    if not profile_path.exists():
        available = ", ".join(list_profile_names())
        raise FileNotFoundError(f"Profile {profile_name!r} not found at {profile_path}. Available: {available}")

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    return safe_name, Thresholds(
        hp_trigger_at_or_below=int(data["hp_trigger_at_or_below"]),
        hp_reset_above=int(data["hp_reset_above"]),
        mp_trigger_at_or_below=int(data["mp_trigger_at_or_below"]),
        mp_reset_above=int(data["mp_reset_above"]),
    )


def list_profile_names() -> list[str]:
    ensure_default_profiles()
    return sorted(path.stem for path in PROFILES.profiles_dir.glob("*.json"))


def format_profile_summary(profile_name: str, thresholds: Thresholds) -> str:
    return (
        f"PROFILE: {profile_name} "
        f"hp<={thresholds.hp_trigger_at_or_below} reset>{thresholds.hp_reset_above} | "
        f"mp<={thresholds.mp_trigger_at_or_below} reset>{thresholds.mp_reset_above}"
    )


def _write_profile_if_missing(profile_name: str, thresholds: Thresholds) -> None:
    profile_path = PROFILES.profiles_dir / f"{profile_name}.json"
    if profile_path.exists():
        return
    profile_path.write_text(json.dumps(asdict(thresholds), indent=2) + "\n", encoding="utf-8")


def _safe_profile_name(profile_name: str) -> str:
    return Path(profile_name).stem.lower().strip()
