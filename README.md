# Multi-Modal Document Intelligence Agent
### Invoice & Form Processing — LangGraph Multi-Agent System

---

## Block Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOCUMENT INPUT                                        │
│              PDF  ·  PNG  ·  JPG  ·  TIFF  ·  Scanned Image                │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   DOCUMENT INGESTION PIPELINE                                │
│                                                                              │
│  ┌──────────────────┐   ┌────────────────────────────┐                      │
│  │  pdf2image       │──▶│  Pillow Pre-Processing     │                      │
│  │  300 DPI         │   │  • Deskew  (OpenCV)        │                      │
│  │  (multi-page)    │   │  • Contrast Enhancement    │                      │
│  └──────────────────┘   │  • Sharpening              │                      │
│                         └────────────────────────────┘                      │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ preprocessed image(s)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLASSIFICATION AGENT          ← NEW                       │
│                                                                              │
│   Image ──▶  VLM  ──▶  Document Type                                        │
│                         ├── Invoice  ──▶  InvoiceSchema                      │
│                         ├── Receipt  ──▶  ReceiptSchema                      │
│                         └── Form     ──▶  FormSchema                         │
│                                                                              │
│   Confidence score attached to document type decision                        │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ (image, doc_type, schema)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTRACTION AGENT                                       │
│                                                                              │
│   Image + Schema ──▶  VLM (Claude / InternVL2-8B / LLaVA-7B)               │
│                        └── Structured Prompt                                 │
│                             └── Pydantic Object                              │
│                                  • invoice_number  • vendor_name             │
│                                  • invoice_date    • due_date                │
│                                  • subtotal        • tax_amount              │
│                                  • total_amount    • line_items[]            │
│                                  • iban            • currency                │
│                                                                              │
│   confidence ≥ threshold                  confidence < threshold             │
│         │                                 OR missing required fields         │
│         │                                           │                        │
│         ▼                                           ▼                        │
│   [skip OCR]                        ┌──────────────────────────────┐        │
│                                     │  OCR FALLBACK  (Tesseract)   │        │
│                                     │  • Text recovery             │        │
│                                     │  • Bounding-box crops        │        │
│                                     │  • Merge with VLM output     │        │
│                                     └──────────────┬───────────────┘        │
└────────────────────────────┬────────────────────────┘────────────────────────┘
                             │ extracted + merged data
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       VALIDATION AGENT                                       │
│                                                                              │
│  ┌───────────────────────────────┐  ┌──────────────────────────────────┐    │
│  │  Rule-Based Checks            │  │  Semantic Checks                 │    │
│  │  • Total = Subtotal + Tax     │  │  • Vendor name matching via      │    │
│  │  • Date format  (ISO 8601)    │  │    ChromaDB + rapidfuzz          │    │
│  │  • IBAN format  (regex)       │  │  • Fuzzy threshold  (≥ 80)       │    │
│  │  • Required field presence    │  │  • Confidence scoring            │    │
│  └──────────────┬────────────────┘  └───────────────────┬──────────────┘    │
│                 └───────────────────┬───────────────────┘                   │
│                                     │                                        │
│              PASS                   │              FAIL                      │
│         ┌───────────┐               │         ┌───────────┐                  │
│         │           │               │         │           │                  │
└─────────┼───────────┼───────────────┼─────────┼───────────┼──────────────────┘
          │           │               │         │           │
          ▼           ▼               ▼         ▼           ▼
   high-conf     low-conf      ┌─────────────────────────────────────────┐
  (≥ threshold) (< threshold)  │        AUTO-CORRECTION AGENT            │
        │             │        │                                         │
        │             │        │  Failed field                           │
        │             │        │    └──▶ Crop image region (bbox)        │
        │             │        │    └──▶ Re-query VLM with crop          │
        │             │        │    └──▶ Update extracted field          │
        │             │        │    Max 2 retry attempts per field       │
        │             │        └─────────────────┬───────────────────────┘
        │             │                          │ re-validate
        │             │                          │
        │             ▼                          ▼ (after max retries)
        │   ┌─────────────────────────────────────────────────────────┐
        │   │              HUMAN REVIEW QUEUE          ← NEW          │
        │   │                                                         │
        │   │  • Document flagged for manual verification             │
        │   │  • UI shows extracted fields + original image           │
        │   │  • Reviewer can approve, edit, or reject                │
        │   │  • Approval routes to storage                           │
        │   └─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SQLITE STORAGE  +  EXPORT                              │
│                                                                              │
│  invoice_records:  document_id · source_path · raw_ocr_text                  │
│                    vlm_extraction · corrections · final_data                  │
│                    validation_status · confidence · doc_type · created_at    │
│                                                                              │
│  audit_log:  ingested → classified → extracted → validated → stored          │
│                                                                              │
│  Export:  JSON  ·  CSV                    ← NEW                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## LangGraph Workflow (State Machine)

```
[START]
   │
   ▼
[ingest] ──▶ [classify] ──▶ [extract] ──▶ [ocr_fallback?] ──▶ [validate]
                                                                    │
               ┌────────────────────────────────────────────────────┤
               │                                                    │
        failed fields?                                       all pass?
               │                                                    │
        yes ◄──┤                                         ┌──────────┤
               │                                         │          │
               ▼                                    high-conf   low-conf
           [correct] ──▶ [validate]  (max 2×)           │          │
                              │                          ▼          ▼
                    still failing?                   [store]  [review_queue]
                              │                          │
                              ▼                         [END]
                       [review_queue]
                              │
                             [END]
```

---

## Project Structure

```
capstone/
├── app.py                     # Streamlit UI entry point
├── main.py                    # CLI entry point
├── config.py                  # All settings via .env
├── requirements.txt
├── .env.example
├── EXECUTION_PLAN.md
│
├── ui/                        # Streamlit UI
│   ├── auth.py
│   ├── styles.py
│   ├── pages/
│   │   ├── login.py
│   │   ├── dashboard.py
│   │   ├── process.py
│   │   ├── review.py          # Human review queue
│   │   ├── history.py
│   │   └── settings.py
│   └── components/
│       ├── sidebar.py
│       ├── metrics.py
│       └── pipeline_status.py
│
├── graph/
│   └── workflow.py            # LangGraph StateGraph definition
│
├── pipeline/
│   ├── ingestion.py           # PDF → PIL images (pdf2image + Pillow)
│   └── ocr.py                 # Tesseract OCR fallback + bbox crops
│
├── agents/
│   ├── classification_agent.py  # NEW — Invoice / Receipt / Form
│   ├── extraction_agent.py      # VLM extraction → Pydantic objects
│   ├── validation_agent.py      # Rule-based + semantic validation
│   └── correction_agent.py      # Focused-crop re-query for failed fields
│
├── models/
│   └── schemas.py             # Pydantic models (InvoiceData, etc.)
│
├── database/
│   └── storage.py             # SQLite CRUD + audit log
│
├── utils/
│   ├── image_processing.py    # Deskew, contrast, base64 encoding
│   └── vendor_matcher.py      # ChromaDB + rapidfuzz vendor lookup
│
└── data/
    ├── samples/               # Place test invoices here
    ├── output/                # JSON / CSV exports
    ├── invoices.db            # SQLite (auto-created)
    └── chroma/                # ChromaDB vectors (auto-created)
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. System dependency: Tesseract
brew install tesseract          # macOS
# sudo apt install tesseract-ocr  # Ubuntu

# 3. Configure
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY

# 4a. Launch UI
streamlit run app.py

# 4b. CLI mode
python main.py data/samples/invoice.pdf
python main.py data/samples/*.png --json
python main.py --list
```

---

## VLM Backends

| Backend | Config | Notes |
|---------|--------|-------|
| `claude` (default) | `ANTHROPIC_API_KEY` required | Best accuracy, cloud API |
| `internvl` | `LOCAL_VLM_MODEL=InternVL2-8B` | GPU required, runs locally |
| `llava` | `LOCAL_VLM_MODEL=llava-7b` | GPU required, runs locally |

Set `VLM_BACKEND=` in `.env` to switch.
