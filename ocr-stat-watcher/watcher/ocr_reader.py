import pytesseract
from config import OCR


pytesseract.pytesseract.tesseract_cmd = OCR.tesseract_path


def read_text(image) -> str:
    config = (
        f"--psm {OCR.tesseract_psm} "
        f"-c tessedit_char_whitelist={OCR.whitelist}"
    )
    text = pytesseract.image_to_string(image, config=config)
    return text.strip()
