"""LangGraph multi-agent workflow for invoice processing."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph
from PIL import Image

from agents import correction_agent, extraction_agent, validation_agent
from config import MAX_CORRECTION_ATTEMPTS
from database import storage
from models.schemas import (
    ExtractionResult,
    ProcessingRecord,
    ValidationResult,
    ValidationStatus,
)
from pipeline import ingestion, ocr


class InvoiceState(TypedDict):
    document_id: str
    source_path: str
    images: list[Image.Image]
    ocr_texts: list[str]
    extraction: ExtractionResult | None
    validation: ValidationResult | None
    correction_attempts: int
    final_status: ValidationStatus | None
    processing_notes: list[str]


def _ingest_node(state: InvoiceState) -> InvoiceState:
    images = ingestion.load_document(state["source_path"])
    state["images"] = images
    state["processing_notes"].append(f"Ingested {len(images)} page(s)")
    storage.log_event(state["document_id"], "ingested", {"pages": len(images)})
    return state


def _ocr_node(state: InvoiceState) -> InvoiceState:
    texts = [ocr.extract_text(img) for img in state["images"]]
    state["ocr_texts"] = texts
    state["processing_notes"].append("OCR complete")
    storage.log_event(state["document_id"], "ocr_complete", {"chars": sum(len(t) for t in texts)})
    return state


def _extract_node(state: InvoiceState) -> InvoiceState:
    combined_ocr = "\n\n--- PAGE BREAK ---\n\n".join(state["ocr_texts"])
    result = extraction_agent.run(state["images"][0], combined_ocr)
    state["extraction"] = result
    state["processing_notes"].append(f"Extracted data (confidence={result.confidence:.2f})")
    storage.log_event(state["document_id"], "extraction_complete", {"confidence": result.confidence})
    return state


def _validate_node(state: InvoiceState) -> InvoiceState:
    result = validation_agent.run(state["extraction"])
    state["validation"] = result
    if result.is_valid:
        state["processing_notes"].append("Validation passed")
    else:
        state["processing_notes"].append(f"Validation failed on: {result.failed_fields}")
    storage.log_event(state["document_id"], "validation", {
        "valid": result.is_valid,
        "failed_fields": result.failed_fields,
    })
    return state


def _correct_node(state: InvoiceState) -> InvoiceState:
    state["correction_attempts"] += 1
    updated = correction_agent.run(state["images"][0], state["extraction"], state["validation"])
    state["extraction"] = updated
    state["processing_notes"].append(f"Correction attempt {state['correction_attempts']}")
    storage.log_event(state["document_id"], "correction", {"attempt": state["correction_attempts"]})
    return state


def _store_node(state: InvoiceState) -> InvoiceState:
    validation = state["validation"]
    if validation and validation.is_valid:
        status = ValidationStatus.VALID
    elif state["correction_attempts"] > 0:
        status = ValidationStatus.CORRECTED
    else:
        status = ValidationStatus.FAILED

    state["final_status"] = status

    corrections = []
    if validation:
        for fv in validation.field_validations:
            if fv.status == ValidationStatus.CORRECTED:
                corrections.append(fv.model_dump())

    record = ProcessingRecord(
        document_id=state["document_id"],
        source_path=state["source_path"],
        raw_ocr_text="\n\n".join(state["ocr_texts"]),
        vlm_extraction=state["extraction"].extracted_data.model_dump() if state["extraction"] else {},
        corrections_applied=corrections,
        final_data=state["extraction"].extracted_data.model_dump() if state["extraction"] else {},
        validation_status=status,
        processing_notes=state["processing_notes"],
    )
    storage.save_record(record)
    storage.log_event(state["document_id"], "stored", {"status": status.value})
    return state


def _should_correct(state: InvoiceState) -> str:
    if state["validation"] and not state["validation"].is_valid:
        if state["correction_attempts"] < MAX_CORRECTION_ATTEMPTS:
            return "correct"
    return "store"


def build_graph() -> StateGraph:
    storage.init_db()
    graph = StateGraph(InvoiceState)

    graph.add_node("ingest", _ingest_node)
    graph.add_node("ocr", _ocr_node)
    graph.add_node("extract", _extract_node)
    graph.add_node("validate", _validate_node)
    graph.add_node("correct", _correct_node)
    graph.add_node("store", _store_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "ocr")
    graph.add_edge("ocr", "extract")
    graph.add_edge("extract", "validate")
    graph.add_conditional_edges("validate", _should_correct, {"correct": "correct", "store": "store"})
    graph.add_edge("correct", "validate")
    graph.add_edge("store", END)

    return graph.compile()


def process_document(path: str) -> InvoiceState:
    graph = build_graph()
    initial_state: InvoiceState = {
        "document_id": str(uuid.uuid4()),
        "source_path": str(path),
        "images": [],
        "ocr_texts": [],
        "extraction": None,
        "validation": None,
        "correction_attempts": 0,
        "final_status": None,
        "processing_notes": [],
    }
    return graph.invoke(initial_state)
