import streamlit as st
from ui.styles import page_header, badge

_PENDING = [
    {
        "id": "INV-003", "file": "form_w9_contractor.pdf",   "type": "Form",
        "confidence": 0.63, "failed_fields": ["vendor_name", "invoice_date"],
        "vendor": "John Doe LLC", "total": "N/A", "flagged_reason": "Low extraction confidence",
        "data": {"vendor_name": "John Doe LLC", "invoice_date": "03/15/2025",
                 "total_amount": None, "invoice_number": "W9-2025"},
    },
    {
        "id": "INV-007", "file": "scan_receipt_blurry.jpg",  "type": "Receipt",
        "confidence": 0.58, "failed_fields": ["total_amount"],
        "vendor": "Unknown Vendor", "total": "$??", "flagged_reason": "Total mismatch after 2 corrections",
        "data": {"vendor_name": "Unknown Vendor", "invoice_date": "2025-03-10",
                 "total_amount": 150.00, "invoice_number": None},
    },
    {
        "id": "INV-011", "file": "invoice_handwritten.tiff", "type": "Invoice",
        "confidence": 0.61, "failed_fields": ["iban"],
        "vendor": "Artisan Works", "total": "$2,200.00", "flagged_reason": "IBAN format invalid",
        "data": {"vendor_name": "Artisan Works", "invoice_date": "2025-03-18",
                 "total_amount": 2200.00, "invoice_number": "AW-0099", "iban": "DE89-XXXX"},
    },
]


def render() -> None:
    page_header("👁️", "Review Queue", "Documents flagged for human verification")

    if "approved" not in st.session_state:
        st.session_state.approved = set()
    if "rejected" not in st.session_state:
        st.session_state.rejected = set()

    pending = [d for d in _PENDING
               if d["id"] not in st.session_state.approved
               and d["id"] not in st.session_state.rejected]

    col_stats = st.columns(3)
    with col_stats[0]:
        st.metric("Pending Review", len(pending))
    with col_stats[1]:
        st.metric("Approved (session)", len(st.session_state.approved))
    with col_stats[2]:
        st.metric("Rejected (session)", len(st.session_state.rejected))

    st.markdown("<br/>", unsafe_allow_html=True)

    if not pending:
        st.success("Review queue is empty — all documents have been processed.")
        return

    for doc in pending:
        conf_pct = int(doc["confidence"] * 100)
        conf_color = "#d97706" if conf_pct >= 60 else "#dc2626"

        with st.expander(
            f"🔍  {doc['file']}  —  {doc['type']}  —  Confidence {conf_pct}%  —  {doc['flagged_reason']}",
            expanded=False,
        ):
            left, right = st.columns([2, 1])

            with left:
                st.markdown("**Extracted Fields** *(edit to correct)*")
                edited = {}
                for k, v in doc["data"].items():
                    edited[k] = st.text_input(
                        k.replace("_", " ").title(),
                        value=str(v) if v is not None else "",
                        key=f"{doc['id']}_{k}",
                    )

            with right:
                st.markdown("**Review Summary**")
                st.markdown(f"- **Doc ID:** {doc['id']}")
                st.markdown(f"- **Type:** {doc['type']}")
                st.markdown(
                    f"- **Confidence:** "
                    f"<span style='color:{conf_color};font-weight:700'>{conf_pct}%</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"- **Reason flagged:** {doc['flagged_reason']}")
                st.markdown("**Failed fields:**")
                for f in doc["failed_fields"]:
                    st.markdown(
                        f"  {badge(f, 'failed')}",
                        unsafe_allow_html=True,
                    )

                st.markdown("<br/>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Approve", key=f"approve_{doc['id']}", use_container_width=True, type="primary"):
                        st.session_state.approved.add(doc["id"])
                        st.toast(f"{doc['id']} approved and stored.", icon="✅")
                        st.rerun()
                with c2:
                    if st.button("❌ Reject", key=f"reject_{doc['id']}", use_container_width=True):
                        st.session_state.rejected.add(doc["id"])
                        st.toast(f"{doc['id']} rejected.", icon="🗑️")
                        st.rerun()
