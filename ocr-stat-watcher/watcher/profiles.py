import argparse
import json
from dataclasses import asdict
from pathlib import Path

from config import POTIONS, PROFILES, THRESHOLDS, PotionConfig, Thresholds


class CharacterProfile:
    def __init__(self, name: str, thresholds: Thresholds, potions: PotionConfig) -> None:
        self.name = name
        self.thresholds = thresholds
        self.potions = potions


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
    _write_profile_if_missing("main", THRESHOLDS, POTIONS)
    _write_profile_if_missing(
        "gins",
        Thresholds(
            hp_trigger_at_or_below=180,
            hp_reset_above=260,
            mp_trigger_at_or_below=80,
            mp_reset_above=140,
        ),
        POTIONS,
    )


def load_profile(profile_name: str) -> CharacterProfile:
    ensure_default_profiles()
    safe_name = _safe_profile_name(profile_name)
    profile_path = PROFILES.profiles_dir / f"{safe_name}.json"
    if not profile_path.exists():
        available = ", ".join(list_profile_names())
        raise FileNotFoundError(f"Profile {profile_name!r} not found at {profile_path}. Available: {available}")

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    return CharacterProfile(
        name=safe_name,
        thresholds=Thresholds(
            hp_trigger_at_or_below=int(data["hp_trigger_at_or_below"]),
            hp_reset_above=int(data["hp_reset_above"]),
            mp_trigger_at_or_below=int(data["mp_trigger_at_or_below"]),
            mp_reset_above=int(data["mp_reset_above"]),
        ),
        potions=PotionConfig(
            hp_potion_name=str(data.get("hp_potion_name", POTIONS.hp_potion_name)),
            hp_potion_heal_amount=int(data.get("hp_potion_heal_amount", POTIONS.hp_potion_heal_amount)),
            hp_burst_max_presses=int(data.get("hp_burst_max_presses", POTIONS.hp_burst_max_presses)),
        ),
    )


def list_profile_names() -> list[str]:
    ensure_default_profiles()
    return sorted(path.stem for path in PROFILES.profiles_dir.glob("*.json"))


def format_profile_summary(profile_name: str, thresholds: Thresholds, potions: PotionConfig | None = None) -> str:
    potion_summary = ""
    if potions is not None:
        potion_summary = (
            f" | hp_potion={potions.hp_potion_name}"
            f" heal={potions.hp_potion_heal_amount}"
            f" burst<={potions.hp_burst_max_presses}x"
        )
    return (
        f"PROFILE: {profile_name} "
        f"hp<={thresholds.hp_trigger_at_or_below} reset>{thresholds.hp_reset_above} | "
        f"mp<={thresholds.mp_trigger_at_or_below} reset>{thresholds.mp_reset_above}"
        f"{potion_summary}"
    )


def _write_profile_if_missing(profile_name: str, thresholds: Thresholds, potions: PotionConfig) -> None:
    profile_path = PROFILES.profiles_dir / f"{profile_name}.json"
    if profile_path.exists():
        return
    profile_data = asdict(thresholds)
    profile_data.update(asdict(potions))
    profile_path.write_text(json.dumps(profile_data, indent=2) + "\n", encoding="utf-8")


def _safe_profile_name(profile_name: str) -> str:
    return Path(profile_name).stem.lower().strip()
