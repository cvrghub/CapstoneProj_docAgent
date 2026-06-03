import streamlit as st

_CSS = """
<style>
/* ── Global ─────────────────────────────────────────────── */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stAppViewContainer"] {background: #f0f4f8;}
[data-testid="stSidebar"] {background: #1a2744 !important;}
[data-testid="stSidebar"] * {color: #e8edf5 !important;}

/* ── Login page ─────────────────────────────────────────── */
.login-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
}
.login-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 48px 40px 40px;
    box-shadow: 0 8px 32px rgba(26,39,68,.15);
    width: 100%;
    max-width: 420px;
    text-align: center;
}
.login-logo {
    font-size: 2.8rem;
    margin-bottom: 4px;
}
.login-title {
    font-size: 1.7rem;
    font-weight: 700;
    color: #1a2744;
    margin: 0 0 4px;
}
.login-subtitle {
    font-size: 0.9rem;
    color: #6b7a99;
    margin-bottom: 32px;
}
.login-hint {
    font-size: 0.8rem;
    color: #9aa5be;
    margin-top: 16px;
}

/* ── Sidebar nav ────────────────────────────────────────── */
.sidebar-logo {
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    padding: 8px 0 4px;
}
.sidebar-user {
    font-size: 0.8rem;
    opacity: 0.65;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,.12);
    margin-bottom: 12px;
}
.sidebar-section {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    opacity: 0.45;
    margin: 16px 0 6px;
}

/* ── Metric cards ───────────────────────────────────────── */
.metric-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(26,39,68,.08);
    border-left: 4px solid;
}
.metric-card.blue  {border-color: #2563eb;}
.metric-card.green {border-color: #16a34a;}
.metric-card.amber {border-color: #d97706;}
.metric-card.red   {border-color: #dc2626;}
.metric-label {font-size:.78rem; color:#6b7a99; text-transform:uppercase; letter-spacing:.8px; margin-bottom:6px;}
.metric-value {font-size:2rem; font-weight:700; color:#1a2744; line-height:1;}
.metric-delta {font-size:.78rem; margin-top:6px;}
.delta-up   {color:#16a34a;}
.delta-down {color:#dc2626;}

/* ── Pipeline stepper ───────────────────────────────────── */
.step-row {display:flex; align-items:center; gap:0; margin: 24px 0;}
.step-item {display:flex; flex-direction:column; align-items:center; flex:1;}
.step-circle {
    width:36px; height:36px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:.85rem; font-weight:700;
}
.step-done    {background:#16a34a; color:#fff;}
.step-active  {background:#2563eb; color:#fff; box-shadow:0 0 0 4px rgba(37,99,235,.2);}
.step-pending {background:#e2e8f0; color:#94a3b8;}
.step-error   {background:#dc2626; color:#fff;}
.step-name  {font-size:.7rem; margin-top:6px; color:#6b7a99; text-align:center;}
.step-line  {flex:1; height:2px; background:#e2e8f0; margin-top:-18px;}
.step-line.done {background:#16a34a;}

/* ── Status badges ──────────────────────────────────────── */
.badge {
    display:inline-block; padding:3px 10px; border-radius:999px;
    font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.5px;
}
.badge-valid     {background:#dcfce7; color:#166534;}
.badge-failed    {background:#fee2e2; color:#991b1b;}
.badge-corrected {background:#fef3c7; color:#92400e;}
.badge-review    {background:#dbeafe; color:#1e40af;}

/* ── Page header ────────────────────────────────────────── */
.page-header {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(26,39,68,.06);
    display: flex;
    align-items: center;
    gap: 12px;
}
.page-header h1 {font-size:1.4rem; font-weight:700; color:#1a2744; margin:0;}
.page-header p  {font-size:.85rem; color:#6b7a99; margin:2px 0 0;}

/* ── Buttons ────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all .15s !important;
}
.stButton > button:hover {transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,.12);}

/* ── Tables ─────────────────────────────────────────────── */
[data-testid="stDataFrame"] {border-radius: 8px; overflow: hidden;}

/* ── Upload zone ────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed #c7d2e7 !important;
    border-radius: 12px !important;
    background: #f8faff !important;
    padding: 12px !important;
}

/* ── Divider ────────────────────────────────────────────── */
.section-divider {
    border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def badge(text: str, kind: str) -> str:
    return f'<span class="badge badge-{kind}">{text}</span>'


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""<div class="page-header">
            <span style="font-size:1.8rem">{icon}</span>
            <div><h1>{title}</h1><p>{subtitle}</p></div>
        </div>""",
        unsafe_allow_html=True,
    )
