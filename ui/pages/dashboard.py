import streamlit as st
from ui.styles import page_header, badge
from ui.components.metrics import render_kpi_row

_RECENT = [
    {"id": "INV-001", "file": "acme_invoice_march.pdf",    "type": "Invoice", "status": "valid",     "confidence": "96%", "vendor": "Acme Corp",          "total": "$4,250.00"},
    {"id": "INV-002", "file": "receipt_amazon_q1.png",     "type": "Receipt", "status": "corrected", "confidence": "81%", "vendor": "Amazon Business",    "total": "$312.45"},
    {"id": "INV-003", "file": "form_w9_contractor.pdf",    "type": "Form",    "status": "review",    "confidence": "63%", "vendor": "John Doe LLC",        "total": "N/A"},
    {"id": "INV-004", "file": "globaltech_inv_0042.pdf",   "type": "Invoice", "status": "valid",     "confidence": "94%", "vendor": "Global Tech Ltd",    "total": "$18,900.00"},
    {"id": "INV-005", "file": "staples_receipt_0312.jpg",  "type": "Receipt", "status": "valid",     "confidence": "89%", "vendor": "Staples",             "total": "$87.32"},
]

_PIPELINE_HEALTH = [
    ("Ingestion",      "✅ Operational"),
    ("Classification", "✅ Operational"),
    ("Extraction",     "✅ Operational"),
    ("OCR Fallback",   "✅ Operational"),
    ("Validation",     "✅ Operational"),
    ("Correction",     "✅ Operational"),
    ("Storage",        "✅ Operational"),
]


def render() -> None:
    page_header("📊", "Dashboard", "Overview of document processing activity")

    render_kpi_row(total=247, success_rate=94.3, pending=8, today=23)

    st.markdown("<br/>", unsafe_allow_html=True)
    left, right = st.columns([2, 1])

    with left:
        st.markdown("#### Recent Activity")
        for doc in _RECENT:
            b = badge(doc["status"], doc["status"])
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1])
                with c1:
                    st.markdown(f"**{doc['file']}**")
                    st.caption(f"{doc['id']}  ·  {doc['vendor']}")
                with c2:
                    st.caption("Type / Confidence")
                    st.markdown(f"{doc['type']}  ·  {doc['confidence']}")
                with c3:
                    st.caption("Total")
                    st.markdown(doc["total"])
                with c4:
                    st.caption("Status")
                    st.markdown(b, unsafe_allow_html=True)

    with right:
        st.markdown("#### Pipeline Health")
        with st.container(border=True):
            for stage, status in _PIPELINE_HEALTH:
                st.markdown(f"**{stage}**")
                st.caption(status)
                st.markdown("<hr style='margin:6px 0;border-color:#f0f4f8'/>", unsafe_allow_html=True)

        st.markdown("#### Document Types (last 30 days)")
        with st.container(border=True):
            st.markdown("🧾 **Invoices**  — 142  (57%)")
            st.progress(0.57)
            st.markdown("🧾 **Receipts**  — 78   (32%)")
            st.progress(0.32)
            st.markdown("📋 **Forms**     — 27   (11%)")
            st.progress(0.11)
