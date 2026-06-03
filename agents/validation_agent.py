"""Validation Agent — rule-based + semantic checks on extracted invoice data."""

from __future__ import annotations

import re
from datetime import datetime

from config import TOTAL_TOLERANCE
from models.schemas import ExtractionResult, FieldValidation, ValidationResult, ValidationStatus
from utils.vendor_matcher import VendorMatcher

_vendor_matcher = VendorMatcher()


def run(extraction: ExtractionResult) -> ValidationResult:
    data = extraction.extracted_data
    validations: list[FieldValidation] = []

    validations.extend(_check_total(data))
    validations.extend(_check_dates(data))
    validations.extend(_check_iban(data))
    validations.extend(_check_vendor(data))

    failed = [v.field for v in validations if v.status == ValidationStatus.FAILED]
    return ValidationResult(
        is_valid=len(failed) == 0,
        field_validations=validations,
        failed_fields=failed,
    )


def _check_total(data) -> list[FieldValidation]:
    results = []
    if data.subtotal is not None and data.tax_amount is not None and data.total_amount is not None:
        expected = round(data.subtotal + data.tax_amount, 2)
        if abs(expected - data.total_amount) > TOTAL_TOLERANCE:
            results.append(FieldValidation(
                field="total_amount",
                status=ValidationStatus.FAILED,
                message=f"Total {data.total_amount} != subtotal {data.subtotal} + tax {data.tax_amount} = {expected}",
            ))
        else:
            results.append(FieldValidation(field="total_amount", status=ValidationStatus.VALID))
    return results


def _check_dates(data) -> list[FieldValidation]:
    results = []
    for field_name in ("invoice_date", "due_date"):
        value = getattr(data, field_name)
        if value is None:
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
            results.append(FieldValidation(field=field_name, status=ValidationStatus.VALID))
        except ValueError:
            results.append(FieldValidation(
                field=field_name,
                status=ValidationStatus.FAILED,
                message=f"Invalid date format: '{value}' (expected YYYY-MM-DD)",
            ))
    return results


def _check_iban(data) -> list[FieldValidation]:
    if data.iban is None:
        return []
    iban = data.iban.replace(" ", "").upper()
    pattern = r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$"
    if re.match(pattern, iban):
        return [FieldValidation(field="iban", status=ValidationStatus.VALID)]
    return [FieldValidation(
        field="iban",
        status=ValidationStatus.FAILED,
        message=f"Invalid IBAN format: {data.iban}",
    )]


def _check_vendor(data) -> list[FieldValidation]:
    if not data.vendor_name:
        return [FieldValidation(
            field="vendor_name",
            status=ValidationStatus.FAILED,
            message="Vendor name is missing",
        )]
    known, matched = _vendor_matcher.is_known_vendor(data.vendor_name)
    if known and matched and matched.lower() != data.vendor_name.lower():
        return [FieldValidation(
            field="vendor_name",
            status=ValidationStatus.VALID,
            message=f"Matched to known vendor: '{matched}'",
            corrected_value=matched,
        )]
    if not known:
        return [FieldValidation(
            field="vendor_name",
            status=ValidationStatus.VALID,
            message="Vendor not in reference DB — accepted as-is",
        )]
    return [FieldValidation(field="vendor_name", status=ValidationStatus.VALID)]
