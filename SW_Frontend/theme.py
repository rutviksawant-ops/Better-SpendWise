"""
theme.py
========
Graphite & Lavender design tokens and shared CSS injection for SpendWise.
Import inject_css() once at the top of every page.
"""

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
BG_DEEP      = "#303038"
BG_SURFACE   = "#383742"
CARD_LOW     = "#454250"
CARD_HIGH    = "#504A60"
BORDER       = "#666078"

TEXT_PRIMARY   = "#F6F2FC"
TEXT_SECONDARY = "#C6C0D3"

LAV_100 = "#E6D9FF"
LAV_200 = "#CBB6FF"
LAV_300 = "#B49AFB"
LAV_400 = "#A88AE8"
LAV_500 = "#8D73D6"
LAV_600 = "#7257B8"

ACC_BLUE      = "#AEBBFF"
ACC_BLUE_DARK = "#929BE8"
ACC_PINK      = "#E6C7F2"
ACC_PURPLE    = "#C5A5D6"

INCOME_COLOR  = "#6EE7B7"   # soft emerald
EXPENSE_COLOR = "#F87171"   # soft red


# ---------------------------------------------------------------------------
# Streamlit custom CSS
# ---------------------------------------------------------------------------
CSS = f"""
<style>
/* ── Root & body ─────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
    background-color: {BG_DEEP};
    color: {TEXT_PRIMARY};
}}

[data-testid="stSidebar"] {{
    background-color: {BG_SURFACE};
    border-right: 1px solid {BORDER};
}}

[data-testid="stSidebar"] * {{
    color: {TEXT_PRIMARY} !important;
}}

/* ── Top toolbar ─────────────────────────────────────────────────────────── */
[data-testid="stHeader"] {{
    background-color: {BG_DEEP};
}}

/* ── Typography ──────────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {{
    color: {LAV_100} !important;
    font-weight: 600;
}}

p, li, span, label {{
    color: {TEXT_PRIMARY};
}}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
[data-testid="stButton"] > button {{
    background: linear-gradient(135deg, {LAV_500}, {LAV_600});
    color: {TEXT_PRIMARY} !important;
    border: none;
    border-radius: 8px;
    padding: 0.45rem 1.2rem;
    font-weight: 600;
    transition: opacity 0.2s;
}}
[data-testid="stButton"] > button:hover {{
    opacity: 0.88;
}}

/* Danger / secondary button override via custom class trick */
button[kind="secondary"] {{
    background: {CARD_HIGH} !important;
    color: {TEXT_SECONDARY} !important;
    border: 1px solid {BORDER} !important;
}}

/* ── Form inputs ─────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stSelectbox"] div[data-baseweb="select"] div {{
    background-color: {CARD_LOW} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {BORDER} !important;
    border-radius: 8px !important;
}}

[data-testid="stSelectbox"] ul {{
    background-color: {CARD_LOW} !important;
}}

/* ── Metric cards ─────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background-color: {CARD_LOW};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1rem 1.2rem;
}}
[data-testid="stMetric"] label {{
    color: {TEXT_SECONDARY} !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {LAV_200} !important;
    font-size: 1.6rem !important;
    font-weight: 700;
}}

/* ── Data table ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    overflow: hidden;
}}

/* ── Expanders ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background-color: {CARD_LOW};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
[data-testid="stExpander"] summary {{
    color: {LAV_200} !important;
    font-weight: 600;
}}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {{
    color: {TEXT_SECONDARY};
    border-bottom: 2px solid transparent;
    padding: 0.5rem 1rem;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {LAV_200} !important;
    border-bottom: 2px solid {LAV_400};
    font-weight: 700;
}}

/* ── Alerts ───────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: 8px;
    border-left-width: 4px;
}}

/* ── Sidebar nav pill ─────────────────────────────────────────────────────── */
.nav-pill {{
    display: block;
    padding: 0.55rem 1rem;
    margin: 0.25rem 0;
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.15s;
}}
.nav-pill:hover {{
    background-color: {CARD_LOW};
    color: {LAV_200};
}}
.nav-pill.active {{
    background: linear-gradient(135deg, {LAV_500}33, {LAV_600}22);
    color: {LAV_100};
    border-left: 3px solid {LAV_400};
}}

/* ── Custom card ─────────────────────────────────────────────────────────── */
.sw-card {{
    background-color: {CARD_LOW};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}}

.sw-badge-income {{
    background-color: #16423066;
    color: {INCOME_COLOR};
    border: 1px solid #6EE7B733;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
}}
.sw-badge-expense {{
    background-color: #4A161666;
    color: {EXPENSE_COLOR};
    border: 1px solid #F8717133;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
}}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {{
    border-color: {BORDER};
    opacity: 0.5;
}}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {BG_DEEP}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
</style>
"""


def inject_css():
    """Call once at the top of each Streamlit page to apply the theme."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
