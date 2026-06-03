"""Extraction Agent — sends image + OCR text to a VLM and parses structured output."""

from __future__ import annotations

import json
import re
from typing import Optional

from PIL import Image

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, VLM_BACKEND
from models.schemas import ExtractionResult, InvoiceData
from utils.image_processing import image_to_base64

_EXTRACTION_PROMPT = """You are an invoice data extraction expert. Given the invoice image and its OCR text, extract the following fields into valid JSON:

{
  "invoice_number": "string or null",
  "vendor_name": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "subtotal": number or null,
  "tax_amount": number or null,
  "total_amount": number or null,
  "currency": "3-letter ISO code",
  "iban": "string or null",
  "payment_terms": "string or null",
  "line_items": [
    {"description": "...", "quantity": number, "unit_price": number, "total": number}
  ]
}

OCR TEXT:
{ocr_text}

Rules:
- Return ONLY the JSON object, no explanation.
- Use null for missing fields, not empty strings.
- Amounts must be plain numbers (no currency symbols).
- Dates must be ISO 8601 (YYYY-MM-DD)."""


def run(image: Image.Image, ocr_text: str) -> ExtractionResult:
    if VLM_BACKEND == "claude":
        return _extract_with_claude(image, ocr_text)
    elif VLM_BACKEND in ("internvl", "llava"):
        return _extract_with_local_vlm(image, ocr_text)
    else:
        raise ValueError(f"Unknown VLM_BACKEND: {VLM_BACKEND}")


def _extract_with_claude(image: Image.Image, ocr_text: str) -> ExtractionResult:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    b64 = image_to_base64(image, fmt="PNG")
    prompt = _EXTRACTION_PROMPT.format(ocr_text=ocr_text[:4000])

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
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

    raw_response = message.content[0].text
    invoice_data, confidence = _parse_vlm_json(raw_response)
    return ExtractionResult(
        raw_ocr_text=ocr_text,
        extracted_data=invoice_data,
        confidence=confidence,
        vlm_response=raw_response,
    )


def _extract_with_local_vlm(image: Image.Image, ocr_text: str) -> ExtractionResult:
    """Stub for InternVL2-8B / LLaVA-7B via HuggingFace transformers."""
    from config import LOCAL_VLM_DEVICE, LOCAL_VLM_MODEL

    try:
        import torch
        from transformers import AutoModel, AutoTokenizer
    except ImportError as e:
        raise ImportError("Install transformers and torch for local VLM support.") from e

    # Load model (cached after first call)
    tokenizer = AutoTokenizer.from_pretrained(LOCAL_VLM_MODEL, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        LOCAL_VLM_MODEL,
        torch_dtype=torch.float16,
        device_map=LOCAL_VLM_DEVICE,
        trust_remote_code=True,
    ).eval()

    prompt = _EXTRACTION_PROMPT.format(ocr_text=ocr_text[:4000])
    # InternVL2 / LLaVA conversation format
    inputs = tokenizer(prompt, return_tensors="pt").to(LOCAL_VLM_DEVICE)
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_new_tokens=1024)
    raw_response = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    invoice_data, confidence = _parse_vlm_json(raw_response)
    return ExtractionResult(
        raw_ocr_text=ocr_text,
        extracted_data=invoice_data,
        confidence=confidence,
        vlm_response=raw_response,
    )


def _parse_vlm_json(text: str) -> tuple[InvoiceData, float]:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return InvoiceData(), 0.0
    try:
        data = json.loads(match.group())
        invoice = InvoiceData(**{k: v for k, v in data.items() if k in InvoiceData.model_fields})
        filled = sum(1 for v in invoice.model_dump().values() if v not in (None, [], {}))
        total_fields = len(InvoiceData.model_fields)
        confidence = filled / total_fields
        return invoice, confidence
    except Exception:
        return InvoiceData(), 0.0
