# OCR Stat Watcher

Small Windows Python project that reads HP/MP from fixed screen regions and presses `z` based on thresholds.

## What this does
- Captures two tiny on-screen regions: HP text and MP text
- Uses Tesseract OCR to read values like `626/857`
- Parses the numbers safely
- Presses `z` when:
  - HP is at or below a configured threshold
  - MP is within a configured range
- Uses read stabilization and cooldowns to avoid bad triggers

## Project structure

```text
ocr-stat-watcher/
├─ README.md
├─ requirements.txt
├─ main.py
├─ config.py
├─ regions.py
├─ watcher/
│  ├─ __init__.py
│  ├─ capture.py
│  ├─ preprocess.py
│  ├─ ocr_reader.py
│  ├─ parser.py
│  ├─ triggers.py
│  └─ debug.py
└─ debug_output/
```

## 1. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Install Tesseract on Windows
Install Tesseract OCR, then confirm the path in `config.py` matches your install:

```python
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 4. Set your screen regions
Edit `regions.py` with the correct coordinates for the HP and MP text.

## 5. Run

```bash
python main.py
```

## First milestone
Before letting it press keys for real, get stable terminal output like:

```text
HP OCR='626/857' parsed=(626, 857) | MP OCR='334/496' parsed=(334, 496)
```

If that is not stable, do not move on yet.

## Tuning tips
- Increase `upscale_factor` if the font is tiny
- Adjust `threshold_value` if OCR is inconsistent
- Keep the game window position and scale fixed
- Save processed images to `debug_output/` if needed while tuning

## Suggested build order

### Phase 1 — OCR only
- Get Tesseract installed
- Verify `tesseract_path`
- Set the two crop regions
- Print parsed values only
- Do not rely on key presses yet

### Phase 2 — Stability
- Tune image preprocessing
- Require matching consecutive reads
- Ignore malformed OCR outputs

### Phase 3 — Actions
- Test `keyboard.press_and_release("z")`
- Verify cooldown behavior
- Test safely in a controlled scenario

### Phase 4 — Polish
- Add optional image dumps for failed OCR
- Add logging
- Add separate HP and MP keys if needed
