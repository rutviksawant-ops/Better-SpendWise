"""
app.py
======
Entry-point for SpendWise — Smart Personal Expense Analyzer.
Run with:  streamlit run app.py   (from SW_Frontend/)

Renders sidebar navigation and delegates to page modules.
"""

import streamlit as st

# ── Path setup (must be first) ────────────────────────────────────────────
import backend_bridge  # noqa: F401  puts SW_Backend on sys.path

# ── Theme ─────────────────────────────────────────────────────────────────
from theme import inject_css, LAV_300, TEXT_SECONDARY, BG_SURFACE, BORDER

st.set_page_config(
    page_title="SpendWise",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 1rem 0 1.5rem 0; text-align: center;">
            <span style="font-size: 2rem;">💜</span>
            <h2 style="margin: 0.3rem 0 0 0; color: {LAV_300}; font-size: 1.3rem;">
                SpendWise
            </h2>
            <p style="color: {TEXT_SECONDARY}; font-size: 0.75rem; margin: 0;">
                Smart Personal Expense Analyzer
            </p>
        </div>
        <hr style="border-color: {BORDER}; margin: 0 0 1rem 0;" />
        """,
        unsafe_allow_html=True,
    )

    PAGES = {
        "📊  Dashboard":     "dashboard",
        "💳  Transactions":  "transactions",
        "🎯  Budgets":       "budgets",
        "📈  Analytics":     "analytics",
    }

    if "active_page" not in st.session_state:
        st.session_state.active_page = "dashboard"

    for label, key in PAGES.items():
        is_active = st.session_state.active_page == key
        btn_style = (
            f"background: linear-gradient(135deg, #8D73D633, #7257B822); "
            f"color: #E6D9FF; border-left: 3px solid #A88AE8;"
            if is_active
            else f"background: transparent; color: {TEXT_SECONDARY}; border-left: 3px solid transparent;"
        )
        if st.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
        ):
            st.session_state.active_page = key
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; font-size:0.7rem; text-align:center;'>"
        f"v1.0 · College Mini-Project</p>",
        unsafe_allow_html=True,
    )

# ── Page routing ──────────────────────────────────────────────────────────
page = st.session_state.active_page

def _render_page(module_name: str) -> None:
    """Import and render one page; show its error instead of a blank screen."""
    try:
        import importlib
        importlib.import_module(f"pages.{module_name}").render()
    except Exception as exc:  # noqa: BLE001 - keep the shell and sidebar alive
        st.error(f"The {module_name.title()} page hit an error: {exc}", icon="❌")
        st.exception(exc)


if page in ("transactions", "dashboard", "budgets", "analytics"):
    _render_page(page)
