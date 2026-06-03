import streamlit as st
from ui.auth import logout

_NAV = [
    ("📊", "Dashboard",        "Overview & metrics"),
    ("🔄", "Process Document", "Upload & extract"),
    ("👁️", "Review Queue",     "Pending approvals"),
    ("📋", "History",          "All records"),
    ("⚙️", "Settings",         "Configuration"),
]


def render_sidebar() -> str:
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">🧾 DocIntel</div>'
            '<div class="sidebar-user">Invoice Intelligence Platform</div>',
            unsafe_allow_html=True,
        )

        username = st.session_state.get("username", "user")
        st.markdown(
            f'<div style="font-size:.8rem;opacity:.7;margin-bottom:16px;">👤 {username}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)

        for icon, label, _ in _NAV:
            is_active = st.session_state.current_page == label
            style = "background:rgba(255,255,255,.12);border-radius:8px;" if is_active else ""
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{label}",
                use_container_width=True,
            ):
                st.session_state.current_page = label
                st.rerun()

        st.markdown("<hr style='border-color:rgba(255,255,255,.1);margin:20px 0'/>", unsafe_allow_html=True)

        if st.button("🚪  Logout", use_container_width=True, key="nav_logout"):
            logout()
            st.rerun()

    return st.session_state.current_page
