import pytesseract
import cv2
from config import OCR


pytesseract.pytesseract.tesseract_cmd = OCR.tesseract_path


def read_text(image) -> str:
    config = (
        f"--psm {OCR.tesseract_psm} "
        f"-c tessedit_char_whitelist={OCR.whitelist}"
    )
    try:
        text = pytesseract.image_to_string(image, config=config, timeout=1.5)
    except RuntimeError as exc:
        print(f"OCR read_text timeout/error: {exc}")
        return ""
    return text.strip()


def read_digits(image) -> str:
    config = "--psm 7 -c tessedit_char_whitelist=0123456789"
    try:
        text = pytesseract.image_to_string(image, config=config, timeout=1.5)
    except RuntimeError as exc:
        print(f"OCR read_digits timeout/error: {exc}")
        return ""
    return "".join(ch for ch in text if ch.isdigit())


def read_digit_components(image) -> str:
    component_map = (image > 0).astype("uint8")
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(component_map, connectivity=8)

    digit_boxes = []
    for label_index in range(1, num_labels):
        x, y, width, height, area = stats[label_index]
        if area < 30 or height < 20:
            continue
        digit_boxes.append((x, y, width, height))

    if not digit_boxes:
        return ""

    digit_boxes.sort(key=lambda box: box[0])
    digits = []
    for x, y, width, height in digit_boxes:
        crop = image[max(y - 4, 0): y + height + 4, max(x - 4, 0): x + width + 4]
        crop = cv2.copyMakeBorder(crop, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=0)

        digit_text = ""
        for psm in (10, 13, 8, 7):
            config = f"--psm {psm} -c tessedit_char_whitelist=0123456789"
            try:
                text = pytesseract.image_to_string(crop, config=config, timeout=1.5)
            except RuntimeError:
                continue
            digit_text = "".join(ch for ch in text if ch.isdigit())
            if digit_text:
                digits.append(digit_text[0])
                break

        if not digit_text:
            return ""

    return "".join(digits)
