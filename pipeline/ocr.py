"""Tesseract OCR baseline — extracts raw text and bounding-box data."""

from __future__ import annotations

from PIL import Image

try:
    import pytesseract
    from pytesseract import Output
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False


def extract_text(image: Image.Image) -> str:
    if not _TESSERACT_AVAILABLE:
        return ""
    return pytesseract.image_to_string(image, config="--psm 6")


def extract_with_boxes(image: Image.Image) -> dict:
    """Return Tesseract data dict with bounding boxes for each word."""
    if not _TESSERACT_AVAILABLE:
        return {}
    return pytesseract.image_to_data(image, output_type=Output.DICT, config="--psm 6")


def crop_region(image: Image.Image, keyword: str, padding: int = 20) -> Image.Image | None:
    """Return a cropped region around the first occurrence of a keyword, or None."""
    if not _TESSERACT_AVAILABLE:
        return None

    data = extract_with_boxes(image)
    for i, word in enumerate(data["text"]):
        if keyword.lower() in word.lower() and int(data["conf"][i]) > 0:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            left = max(0, x - padding)
            top = max(0, y - padding)
            right = min(image.width, x + w + padding)
            bottom = min(image.height, y + h + padding)
            return image.crop((left, top, right, bottom))
    return None
