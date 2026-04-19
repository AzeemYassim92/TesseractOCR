from pathlib import Path
import cv2


DEBUG_DIR = Path("debug_output")
DEBUG_DIR.mkdir(exist_ok=True)


def save_debug_image(filename: str, image) -> None:
    path = DEBUG_DIR / filename
    cv2.imwrite(str(path), image)
