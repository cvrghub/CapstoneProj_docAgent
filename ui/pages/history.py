import json
import streamlit as st
import pandas as pd
from ui.styles import page_header

_RECORDS = [
    {"ID": "INV-001", "File": "acme_invoice_march.pdf",    "Type": "Invoice", "Vendor": "Acme Corp",       "Total": 4250.00,  "Status": "valid",     "Confidence": "96%", "Date": "2025-03-15"},
    {"ID": "INV-002", "File": "receipt_amazon_q1.png",     "Type": "Receipt", "Vendor": "Amazon Business", "Total": 312.45,   "Status": "corrected", "Confidence": "81%", "Date": "2025-03-14"},
    {"ID": "INV-003", "File": "form_w9_contractor.pdf",    "Type": "Form",    "Vendor": "John Doe LLC",    "Total": None,     "Status": "review",    "Confidence": "63%", "Date": "2025-03-14"},
    {"ID": "INV-004", "File": "globaltech_inv_0042.pdf",   "Type": "Invoice", "Vendor": "Global Tech Ltd", "Total": 18900.00, "Status": "valid",     "Confidence": "94%", "Date": "2025-03-13"},
    {"ID": "INV-005", "File": "staples_receipt_0312.jpg",  "Type": "Receipt", "Vendor": "Staples",         "Total": 87.32,    "Status": "valid",     "Confidence": "89%", "Date": "2025-03-13"},
    {"ID": "INV-006", "File": "dell_invoice_q1_2025.pdf",  "Type": "Invoice", "Vendor": "Dell Technologies","Total": 5499.00, "Status": "valid",     "Confidence": "97%", "Date": "2025-03-12"},
    {"ID": "INV-007", "File": "scan_receipt_blurry.jpg",   "Type": "Receipt", "Vendor": "Unknown Vendor",  "Total": 150.00,   "Status": "review",    "Confidence": "58%", "Date": "2025-03-12"},
    {"ID": "INV-008", "File": "officedepot_march.pdf",     "Type": "Invoice", "Vendor": "Office Depot",    "Total": 340.90,   "Status": "valid",     "Confidence": "91%", "Date": "2025-03-11"},
]


def render() -> None:
    page_header("📋", "History", "All processed documents with full audit trail")

    df = pd.DataFrame(_RECORDS)

    # ── Filters ───────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 2])
    with f1:
        search = st.text_input("🔍 Search", placeholder="File name or vendor…", label_visibility="collapsed")
    with f2:
        types = ["All"] + sorted(df["Type"].unique().tolist())
        type_filter = st.selectbox("Type", types, label_visibility="collapsed")
    with f3:
        statuses = ["All"] + sorted(df["Status"].unique().tolist())
        status_filter = st.selectbox("Status", statuses, label_visibility="collapsed")
    with f4:
        _, dl_col = st.columns([1, 1])

    # ── Apply filters ─────────────────────────────────────────
    filtered = df.copy()
    if search:
        mask = (
            filtered["File"].str.contains(search, case=False)
            | filtered["Vendor"].str.contains(search, case=False)
        )
        filtered = filtered[mask]
    if type_filter != "All":
        filtered = filtered[filtered["Type"] == type_filter]
    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    st.caption(f"Showing {len(filtered)} of {len(df)} records")

    # ── Table ─────────────────────────────────────────────────
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total": st.column_config.NumberColumn("Total", format="$%.2f"),
            "Status": st.column_config.TextColumn("Status"),
        },
    )

    # ── Export ────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    ec1, ec2, _ = st.columns([1, 1, 3])
    with ec1:
        st.download_button(
            "⬇️ Export CSV",
            data=filtered.to_csv(index=False),
            file_name="invoice_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with ec2:
        st.download_button(
            "⬇️ Export JSON",
            data=filtered.to_json(orient="records", indent=2),
            file_name="invoice_history.json",
            mime="application/json",
            use_container_width=True,
        )
