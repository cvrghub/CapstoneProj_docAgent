from typing import Optional
import streamlit as st

_STAGES = [
    ("Ingest",    "📥"),
    ("Classify",  "🏷️"),
    ("Extract",   "🔍"),
    ("OCR Check", "📄"),
    ("Validate",  "✅"),
    ("Route",     "🔀"),
    ("Store",     "💾"),
]


def render(current_stage: Optional[str] = None, failed_stage: Optional[str] = None) -> None:
    """
    current_stage: name of the stage currently running (shown as active/spinning)
    failed_stage:  name of the stage that failed (shown in red)
    Pass None for both to render all-pending (pre-run state).
    """
    stage_names = [s[0] for s in _STAGES]

    active_idx = stage_names.index(current_stage) if current_stage in stage_names else -1
    failed_idx = stage_names.index(failed_stage) if failed_stage in stage_names else -1

    circles = []
    for i, (name, icon) in enumerate(_STAGES):
        if failed_idx == i:
            cls, label = "step-error", "✗"
        elif i < active_idx:
            cls, label = "step-done", "✓"
        elif i == active_idx:
            cls, label = "step-active", icon
        else:
            cls, label = "step-pending", str(i + 1)

        line_cls = "done" if i < active_idx else ""
        line_html = f'<div class="step-line {line_cls}"></div>' if i < len(_STAGES) - 1 else ""

        circles.append(
            f'<div class="step-item">'
            f'<div class="step-circle {cls}">{label}</div>'
            f'<div class="step-name">{name}</div>'
            f'</div>'
            + line_html
        )

    html = '<div class="step-row">' + "".join(circles) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_complete(success: bool = True) -> None:
    if success:
        render(current_stage=None, failed_stage=None)
        st.success("Pipeline completed successfully.")
    else:
        st.error("Pipeline completed with errors — document sent to review queue.")
