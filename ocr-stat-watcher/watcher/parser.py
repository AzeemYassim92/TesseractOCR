import re
from typing import Optional, Tuple


STAT_PATTERN = re.compile(r"(\d+)\s*/\s*(\d+)")


def parse_stat_pair(text: str) -> Optional[Tuple[int, int]]:
    match = STAT_PATTERN.search(text)
    if not match:
        return None

    current_value = int(match.group(1))
    max_value = int(match.group(2))

    if current_value < 0 or max_value <= 0 or current_value > max_value:
        return None

    return current_value, max_value
