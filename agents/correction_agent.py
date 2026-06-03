"""Auto-Correction Agent — re-queries the VLM with a focused crop on failed fields."""

from __future__ import annotations

import json
import re

from PIL import Image

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_CORRECTION_ATTEMPTS, VLM_BACKEND
from models.schemas import (
    ExtractionResult,
    FieldValidation,
    ValidationResult,
    ValidationStatus,
)
from pipeline.ocr import crop_region
from utils.image_processing import image_to_base64

_CORRECTION_PROMPT = """The following field in an invoice could not be validated: {field}

Current extracted value: {current_value}
Validation error: {error_message}

Please look carefully at the provided image crop and re-extract ONLY the "{field}" field.
Return a single JSON object: {{"field": "{field}", "value": <corrected value or null>}}

Rules:
- Amounts must be plain numbers.
- Dates must be ISO 8601 (YYYY-MM-DD).
- Return ONLY the JSON."""


def run(
    image: Image.Image,
    extraction: ExtractionResult,
    validation: ValidationResult,
) -> ExtractionResult:
    updated_data = extraction.extracted_data.model_copy(deep=True)
    corrections_log: list[FieldValidation] = []

    for field in validation.failed_fields:
        fv = next((v for v in validation.field_validations if v.field == field), None)
        current_value = str(getattr(updated_data, field, ""))
        error_msg = fv.message if fv else ""

        corrected_value = _attempt_correction(image, field, current_value, error_msg)
        if corrected_value is not None:
            try:
                setattr(updated_data, field, corrected_value)
                corrections_log.append(FieldValidation(
                    field=field,
                    status=ValidationStatus.CORRECTED,
                    original_value=current_value,
                    corrected_value=str(corrected_value),
                ))
            except Exception:
                pass

    return ExtractionResult(
        raw_ocr_text=extraction.raw_ocr_text,
        extracted_data=updated_data,
        confidence=extraction.confidence,
        vlm_response=extraction.vlm_response,
    )


def _attempt_correction(image: Image.Image, field: str, current: str, error: str):
    crop = crop_region(image, _field_to_keyword(field)) or image

    prompt = _CORRECTION_PROMPT.format(
        field=field,
        current_value=current,
        error_message=error,
    )

    if VLM_BACKEND == "claude":
        return _correct_with_claude(crop, prompt, field)
    return None


def _correct_with_claude(crop: Image.Image, prompt: str, field: str):
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    b64 = image_to_base64(crop, fmt="PNG")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    raw = message.content[0].text
    match = re.search(r"\{[\s\S]*?\}", raw)
    if not match:
        return None
    try:
        obj = json.loads(match.group())
        return obj.get("value")
    except Exception:
        return None


_FIELD_KEYWORDS = {
    "total_amount": "total",
    "subtotal": "subtotal",
    "tax_amount": "tax",
    "invoice_date": "date",
    "due_date": "due",
    "invoice_number": "invoice",
    "vendor_name": "vendor",
    "iban": "iban",
}


def _field_to_keyword(field: str) -> str:
    return _FIELD_KEYWORDS.get(field, field.replace("_", " "))
