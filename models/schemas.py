from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: float


class ValidationStatus(str, Enum):
    VALID = "valid"
    FAILED = "failed"
    CORRECTED = "corrected"


class FieldValidation(BaseModel):
    field: str
    status: ValidationStatus
    message: Optional[str] = None
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None


class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    line_items: list[LineItem] = Field(default_factory=list)
    iban: Optional[str] = None
    payment_terms: Optional[str] = None

    @field_validator("total_amount", "subtotal", "tax_amount", mode="before")
    @classmethod
    def parse_amount(cls, v):
        if isinstance(v, str):
            cleaned = v.replace(",", "").replace("$", "").replace("€", "").strip()
            return float(cleaned) if cleaned else None
        return v


class ExtractionResult(BaseModel):
    raw_ocr_text: str
    extracted_data: InvoiceData
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    vlm_response: Optional[str] = None


class ValidationResult(BaseModel):
    is_valid: bool
    field_validations: list[FieldValidation] = Field(default_factory=list)
    failed_fields: list[str] = Field(default_factory=list)


class ProcessingRecord(BaseModel):
    document_id: str
    source_path: str
    raw_ocr_text: str
    vlm_extraction: dict
    corrections_applied: list[dict] = Field(default_factory=list)
    final_data: dict
    validation_status: ValidationStatus
    processing_notes: list[str] = Field(default_factory=list)
