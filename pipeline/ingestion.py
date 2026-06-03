"""Converts PDF/image files into pre-processed PIL images ready for OCR and VLM."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Union

from PIL import Image

from config import OCR_DPI
from utils.image_processing import deskew, enhance_contrast


def load_document(path: Union[str, Path]) -> list[Image.Image]:
    """Return a list of preprocessed PIL images (one per page for PDFs)."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _pdf_to_images(path)
    elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
        img = Image.open(path).convert("RGB")
        return [_preprocess(img)]
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _pdf_to_images(path: Path) -> list[Image.Image]:
    try:
        from pdf2image import convert_from_path
    except ImportError as e:
        raise ImportError("Install pdf2image: pip install pdf2image") from e

    pages = convert_from_path(str(path), dpi=OCR_DPI)
    return [_preprocess(p.convert("RGB")) for p in pages]


def _preprocess(img: Image.Image) -> Image.Image:
    img = deskew(img)
    img = enhance_contrast(img)
    return img
