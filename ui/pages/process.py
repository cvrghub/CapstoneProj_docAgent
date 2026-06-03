import time
import streamlit as st
from ui.styles import page_header, badge
from ui.components import pipeline_status

_MOCK_RESULT = {
    "doc_type": "Invoice",
    "classification_confidence": 0.97,
    "extraction_confidence": 0.92,
    "validation_status": "valid",
    "corrections": 0,
    "data": {
        "invoice_number":  "INV-2025-00487",
        "vendor_name":     "Acme Corp",
        "invoice_date":    "2025-03-15",
        "due_date":        "2025-04-15",
        "currency":        "USD",
        "subtotal":        3800.00,
        "tax_amount":      380.00,
        "total_amount":    4180.00,
        "iban":            None,
        "payment_terms":   "Net 30",
    },
    "line_items": [
        {"description": "Software Licence Q1", "qty": 1, "unit_price": 2500.00, "total": 2500.00},
        {"description": "Support & Maintenance", "qty": 3, "unit_price": 350.00, "total": 1050.00},
        {"description": "Setup Fee",             "qty": 1, "unit_price": 250.00, "total": 250.00},
    ],
}


def _run_mock_pipeline(placeholder) -> dict:
    stages = [
        ("Ingest",    "Reading and pre-processing document pages…"),
        ("Classify",  "Identifying document type with VLM…"),
        ("Extract",   "Extracting structured fields…"),
        ("OCR Check", "Confidence high — OCR fallback skipped"),
        ("Validate",  "Running rule-based and semantic checks…"),
        ("Route",     "Confidence 92% — routing to auto-approve"),
        ("Store",     "Writing to database with audit trail…"),
    ]
    for i, (stage, msg) in enumerate(stages):
        with placeholder.container():
            pipeline_status.render(current_stage=stage)
            st.caption(f"⟳  {msg}")
        time.sleep(0.6)
    return _MOCK_RESULT


def _show_results(result: dict) -> None:
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("### Extraction Results")

    tab_fields, tab_items, tab_validation, tab_export = st.tabs(
        ["📋 Extracted Fields", "🗒️ Line Items", "✅ Validation", "⬇️ Export"]
    )

    data = result["data"]

    with tab_fields:
        st.markdown(
            f"""
            **Document Type:** {result['doc_type']}
            &nbsp;&nbsp;|&nbsp;&nbsp;
            **Classification Confidence:** {result['classification_confidence']*100:.0f}%
            &nbsp;&nbsp;|&nbsp;&nbsp;
            **Extraction Confidence:** {result['extraction_confidence']*100:.0f}%
            """
        )
        st.divider()
        c1, c2 = st.columns(2)
        fields_left = [
            ("Invoice Number", data["invoice_number"]),
            ("Vendor Name",    data["vendor_name"]),
            ("Invoice Date",   data["invoice_date"]),
            ("Due Date",       data["due_date"]),
            ("Payment Terms",  data["payment_terms"]),
        ]
        fields_right = [
            ("Currency",    data["currency"]),
            ("Subtotal",    f"${data['subtotal']:,.2f}"),
            ("Tax Amount",  f"${data['tax_amount']:,.2f}"),
            ("Total",       f"${data['total_amount']:,.2f}"),
            ("IBAN",        data["iban"] or "—"),
        ]
        with c1:
            for k, v in fields_left:
                st.text_input(k, value=str(v) if v else "—", disabled=True)
        with c2:
            for k, v in fields_right:
                st.text_input(k, value=str(v) if v else "—", disabled=True)

    with tab_items:
        if result["line_items"]:
            import pandas as pd
            st.dataframe(
                pd.DataFrame(result["line_items"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No line items extracted.")

    with tab_validation:
        st.markdown(
            f"**Overall Status:** {badge(result['validation_status'], result['validation_status'])}",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Auto-Corrections Applied:** {result['corrections']}")
        st.markdown("**Field Checks:**")
        checks = [
            ("total_amount",   "valid",   "3800 + 380 = 4180 ✓"),
            ("invoice_date",   "valid",   "ISO 8601 format ✓"),
            ("due_date",       "valid",   "ISO 8601 format ✓"),
            ("vendor_name",    "valid",   "Matched: 'Acme Corp' (score 100)"),
        ]
        import pandas as pd
        st.dataframe(
            pd.DataFrame(checks, columns=["Field", "Status", "Detail"]),
            use_container_width=True,
            hide_index=True,
        )

    with tab_export:
        col1, col2 = st.columns(2)
        import json, pandas as pd
        with col1:
            json_str = json.dumps({**data, "line_items": result["line_items"]}, indent=2)
            st.download_button(
                "⬇️ Download JSON",
                data=json_str,
                file_name="extracted_invoice.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            csv_str = pd.DataFrame([data]).to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                data=csv_str,
                file_name="extracted_invoice.csv",
                mime="text/csv",
                use_container_width=True,
            )


def render() -> None:
    page_header("🔄", "Process Document", "Upload an invoice, receipt, or form to extract structured data")

    if "process_result" not in st.session_state:
        st.session_state.process_result = None
    if "process_running" not in st.session_state:
        st.session_state.process_running = False

    uploaded = st.file_uploader(
        "Drop a file here or click to browse",
        type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
        help="Supported: PDF, PNG, JPG, TIFF, BMP",
        key="doc_upload",
    )

    if uploaded:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**Uploaded:** `{uploaded.name}`  ({uploaded.size // 1024} KB)")
        with c2:
            run = st.button("▶  Run Pipeline", type="primary", use_container_width=True)

        if run:
            st.session_state.process_result = None
            st.session_state.process_running = True
            placeholder = st.empty()
            result = _run_mock_pipeline(placeholder)
            placeholder.empty()
            st.session_state.process_result = result
            st.session_state.process_running = False

    elif st.session_state.process_result is None:
        st.markdown("<br/>", unsafe_allow_html=True)
        with st.container(border=True):
            pipeline_status.render()
            st.caption("Pipeline ready — upload a document to begin.")

    if st.session_state.process_result:
        pipeline_status.render(current_stage=None)
        st.success("Document processed successfully.")
        _show_results(st.session_state.process_result)
