"""Classification Agent — identifies document type before extraction.

Supported types: invoice | receipt | form
Each type maps to a different Pydantic extraction schema.
"""

from __future__ import annotations

import json
import re

from PIL import Image

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, VLM_BACKEND
from utils.image_processing import image_to_base64

_SCHEMA_MAP = {
    "invoice": "InvoiceData",
    "receipt": "ReceiptData",
    "form":    "FormData",
}

_CLASSIFICATION_PROMPT = """Look at this document image and classify it.

Return a single JSON object and nothing else:
{"doc_type": "invoice|receipt|form", "confidence": 0.0-1.0, "reasoning": "one sentence"}

- invoice: a formal vendor invoice with invoice number, line items, and totals
- receipt: a point-of-sale or purchase receipt (simpler format, often from retail)
- form: a structured form such as W-9, expense report, or intake form"""


class ClassificationResult:
    def __init__(self, doc_type: str, confidence: float, schema_name: str, reasoning: str = ""):
        self.doc_type = doc_type
        self.confidence = confidence
        self.schema_name = schema_name
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return f"ClassificationResult(doc_type={self.doc_type!r}, confidence={self.confidence:.2f})"


def run(image: Image.Image) -> ClassificationResult:
    if VLM_BACKEND == "claude":
        return _classify_with_claude(image)
    return _fallback_classify()


def _classify_with_claude(image: Image.Image) -> ClassificationResult:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    b64 = image_to_base64(image, fmt="PNG")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                {"type": "text", "text": _CLASSIFICATION_PROMPT},
            ],
        }],
    )
    raw = message.content[0].text
    return _parse_response(raw)


def _parse_response(text: str) -> ClassificationResult:
    match = re.search(r"\{[\s\S]*?\}", text)
    if match:
        try:
            obj = json.loads(match.group())
            doc_type = obj.get("doc_type", "invoice").lower()
            confidence = float(obj.get("confidence", 0.7))
            reasoning = obj.get("reasoning", "")
            schema = _SCHEMA_MAP.get(doc_type, "InvoiceData")
            return ClassificationResult(doc_type, confidence, schema, reasoning)
        except Exception:
            pass
    return _fallback_classify()


def _fallback_classify() -> ClassificationResult:
    return ClassificationResult("invoice", 0.5, "InvoiceData", "Fallback — defaulting to invoice")
