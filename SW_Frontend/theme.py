
"""
theme.py
========
SpendWise — Graphite, Deep Purple & Bold Sticker-inspired theme.
Import inject_css() once at the top of the app.
"""

# ---------------------------------------------------------------------------
# Design tokens — existing names retained for page compatibility
# ---------------------------------------------------------------------------

BG_DEEP = "#373738"
BG_SURFACE = "#2B2A2E"
CARD_LOW = "#414044"
CARD_HIGH = "#4B4654"
BORDER = "#5C5863"

TEXT_PRIMARY = "#F3F0F7"
TEXT_SECONDARY = "#BDB7C7"

LAV_100 = "#E8DDF7"
LAV_200 = "#C5A8F0"
LAV_300 = "#AA83DF"
LAV_400 = "#9068CC"
LAV_500 = "#7046A8"
LAV_600 = "#503078"

ACC_BLUE = "#9DB8E0"
ACC_BLUE_DARK = "#7898C9"
ACC_PINK = "#DDAED0"
ACC_PURPLE = "#B99AD9"
ACC_MINT = "#9CD5BA"
ACC_YELLOW = "#E5D19A"

INCOME_COLOR = "#78D6AF"
EXPENSE_COLOR = "#F08A9A"


# ---------------------------------------------------------------------------
# Shared Streamlit CSS
# ---------------------------------------------------------------------------

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Figtree:wght@400;500;600;700;800&display=swap');

:root {{
    color-scheme: dark;
    --sw-bg: {BG_DEEP};
    --sw-surface: {BG_SURFACE};
    --sw-card: {CARD_LOW};
    --sw-card-raised: {CARD_HIGH};
    --sw-purple: {LAV_500};
    --sw-purple-light: {LAV_300};
    --sw-border: {BORDER};
    --sw-text: {TEXT_PRIMARY};
    --sw-muted: {TEXT_SECONDARY};
}}

/* ── Application canvas ─────────────────────────────────────────────── */

html,
body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {{
    background-color: {BG_DEEP} !important;
    color: {TEXT_PRIMARY} !important;
    font-family: "Figtree", "Segoe UI", sans-serif;
}}

[data-testid="stMainBlockContainer"] {{
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}}

/* ── Typography ─────────────────────────────────────────────────────── */

h1, h2, h3, h4, h5, h6,
[data-testid="stHeading"] {{
    font-family: "Bricolage Grotesque", "Figtree", sans-serif !important;
    color: {TEXT_PRIMARY} !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
}}

h1 {{
    font-size: clamp(2rem, 3vw, 2.8rem) !important;
    letter-spacing: -0.04em;
}}

h2 {{
    font-size: 1.65rem !important;
}}

h3 {{
    font-size: 1.25rem !important;
}}

p, li, label,
[data-testid="stMarkdownContainer"] {{
    color: {TEXT_PRIMARY};
    font-family: "Figtree", "Segoe UI", sans-serif;
}}

small,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {{
    color: {TEXT_SECONDARY} !important;
}}

a {{
    color: {LAV_200} !important;
}}

::selection {{
    background: {LAV_500};
    color: #FFFFFF;
}}

/* ── Sidebar ────────────────────────────────────────────────────────── */

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {{
    background-color: {BG_SURFACE} !important;
}}

[data-testid="stSidebar"] {{
    border-right: 1px solid {BORDER};
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {{
    color: {TEXT_PRIMARY};
}}

[data-testid="stSidebar"] hr {{
    border-color: {BORDER};
    opacity: 0.8;
}}

/* Sidebar buttons: dark surfaces with purple hover */

[data-testid="stSidebar"] [data-testid="stButton"] > button {{
    background: transparent !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid transparent !important;
    border-radius: 13px !important;
    text-align: left;
    box-shadow: none !important;
}}

[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
    background: #43374F !important;
    border-color: #695187 !important;
    color: #FFFFFF !important;
}}

/* ── Header and toolbar ─────────────────────────────────────────────── */

[data-testid="stHeader"] {{
    background: {BG_DEEP} !important;
}}

[data-testid="stToolbar"] {{
    right: 1rem;
}}

[data-testid="stDecoration"] {{
    background: {LAV_500} !important;
}}

/* ── Primary buttons ────────────────────────────────────────────────── */

[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid="stDownloadButton"] > button {{
    background: {LAV_500} !important;
    color: #FFFFFF !important;
    border: 1px solid {LAV_400} !important;
    border-radius: 14px !important;
    padding: 0.5rem 1.1rem;
    min-height: 2.6rem;
    font-family: "Figtree", sans-serif;
    font-weight: 700 !important;
    box-shadow: 0 3px 0 #432764 !important;
    transition: background-color 0.18s ease,
                transform 0.18s ease,
                box-shadow 0.18s ease;
}}

[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover {{
    background: {LAV_400} !important;
    border-color: {LAV_200} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 0 #432764 !important;
}}

[data-testid="stButton"] > button:active,
[data-testid="stFormSubmitButton"] > button:active {{
    transform: translateY(1px);
    box-shadow: 0 1px 0 #432764 !important;
}}

[data-testid="stButton"] > button:focus-visible,
[data-testid="stFormSubmitButton"] > button:focus-visible {{
    outline: 2px solid {LAV_200} !important;
    outline-offset: 3px;
}}

/* Secondary buttons */

[data-testid="stButton"] > button[kind="secondary"],
[data-testid="stFormSubmitButton"] > button[kind="secondary"] {{
    background: {CARD_LOW} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BORDER} !important;
    box-shadow: none !important;
}}

[data-testid="stButton"] > button[kind="secondary"]:hover {{
    background: #51475E !important;
    border-color: {LAV_400} !important;
}}

/* ── Inputs ──────────────────────────────────────────────────────────── */

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea {{
    background: #302F33 !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    caret-color: {LAV_200};
}}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{
    color: #938C9D !important;
}}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stDateInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: {LAV_400} !important;
    box-shadow: 0 0 0 1px {LAV_400} !important;
}}

/* Input stepper buttons */

[data-testid="stNumberInput"] button {{
    background: {CARD_HIGH} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {BORDER} !important;
}}

/* Select boxes and multiselects */

[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
    background: #302F33 !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {BORDER} !important;
    border-radius: 12px !important;
}}

[data-testid="stSelectbox"] input,
[data-testid="stMultiSelect"] input {{
    color: {TEXT_PRIMARY} !important;
}}

[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="select"] ul {{
    background: {CARD_HIGH} !important;
    border: 1px solid {BORDER} !important;
}}

[data-baseweb="menu"] li {{
    background: {CARD_HIGH} !important;
    color: {TEXT_PRIMARY} !important;
}}

[data-baseweb="menu"] li:hover {{
    background: #5A486C !important;
}}

[data-baseweb="tag"] {{
    background: {LAV_500} !important;
    color: #FFFFFF !important;
}}

/* Checkbox, radio, and widget labels */

[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stWidgetLabel"] p {{
    color: {TEXT_PRIMARY} !important;
}}

/* ── Metric cards ───────────────────────────────────────────────────── */

[data-testid="stMetric"] {{
    background: {CARD_LOW} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 20px !important;
    padding: 1.1rem 1.25rem !important;
    box-shadow: 0 4px 0 rgba(20, 18, 24, 0.20) !important;
}}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {{
    color: {TEXT_SECONDARY} !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
}}

[data-testid="stMetricValue"] {{
    color: {LAV_200} !important;
    font-family: "Bricolage Grotesque", sans-serif !important;
    font-size: 1.7rem !important;
    font-weight: 800 !important;
}}

[data-testid="stMetricDelta"] {{
    font-size: 0.82rem;
}}

/* ── Data tables ────────────────────────────────────────────────────── */

[data-testid="stDataFrame"],
[data-testid="stTable"] {{
    background: {CARD_LOW} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 15px !important;
    overflow: hidden;
}}

[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
    background: {CARD_LOW} !important;
}}

/* ── Expanders ──────────────────────────────────────────────────────── */

[data-testid="stExpander"] {{
    background: {CARD_LOW} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    overflow: hidden;
}}

[data-testid="stExpander"] summary {{
    color: {TEXT_PRIMARY} !important;
    font-weight: 700;
}}

[data-testid="stExpander"] summary:hover {{
    color: {LAV_200} !important;
}}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background: {CARD_LOW} !important;
}}

/* ── Tabs ───────────────────────────────────────────────────────────── */

[data-testid="stTabs"] [role="tab"] {{
    color: {TEXT_SECONDARY} !important;
    border-bottom: 2px solid transparent;
    padding: 0.65rem 1rem;
    font-weight: 600;
}}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {LAV_200} !important;
    border-bottom: 2px solid {LAV_400} !important;
    font-weight: 800;
}}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    background: {LAV_400} !important;
}}

/* ── Alerts ─────────────────────────────────────────────────────────── */

[data-testid="stAlert"] {{
    background: {CARD_LOW} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 15px !important;
}}

[data-testid="stAlert"] p {{
    color: {TEXT_PRIMARY} !important;
}}

/* ── Progress bars ──────────────────────────────────────────────────── */

[data-testid="stProgressBar"] > div {{
    background: #29272E !important;
    border-radius: 999px;
    overflow: hidden;
}}

[data-testid="stProgressBar"] > div > div {{
    background: {LAV_400} !important;
    border-radius: 999px;
}}

/* ── Custom card helpers ────────────────────────────────────────────── */

.sw-card {{
    background: {CARD_LOW};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: {TEXT_PRIMARY};
    box-shadow: 0 4px 0 rgba(20, 18, 24, 0.20);
}}

.sw-card-lavender {{
    background: #443650;
    border: 1px solid #71568C;
    border-radius: 20px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: {TEXT_PRIMARY};
    box-shadow: 0 4px 0 rgba(20, 18, 24, 0.18);
}}

.sw-card-blue {{
    background: #35404F;
    border: 1px solid #5D7393;
    border-radius: 20px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: {TEXT_PRIMARY};
}}

.sw-card-pink {{
    background: #493642;
    border: 1px solid #79566F;
    border-radius: 20px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    color: {TEXT_PRIMARY};
}}

/* Sticker-inspired labels */

.sw-sticker {{
    display: inline-block;
    padding: 0.35rem 0.8rem;
    background: {LAV_200};
    color: #292033 !important;
    border: 2px solid #292033;
    border-radius: 12px;
    font-family: "Bricolage Grotesque", sans-serif;
    font-weight: 800;
    box-shadow: 3px 3px 0 #211D26;
    transform: rotate(-2deg);
}}

.sw-sticker-blue {{
    background: {ACC_BLUE};
    color: #242A35 !important;
}}

.sw-sticker-pink {{
    background: {ACC_PINK};
    color: #382533 !important;
}}

.sw-sticker-mint {{
    background: {ACC_MINT};
    color: #203B30 !important;
}}

.sw-section-label {{
    color: {LAV_200} !important;
    font-family: "Bricolage Grotesque", sans-serif;
    font-weight: 800;
    font-size: 0.78rem;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}}

/* Transaction badges */

.sw-badge-income {{
    display: inline-block;
    background: #244638;
    color: {INCOME_COLOR} !important;
    border: 1px solid #3C765B;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 0.78rem;
    font-weight: 800;
}}

.sw-badge-expense {{
    display: inline-block;
    background: #4D3039;
    color: {EXPENSE_COLOR} !important;
    border: 1px solid #80505D;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 0.78rem;
    font-weight: 800;
}}

/* ── Plotly chart containers ────────────────────────────────────────── */

[data-testid="stPlotlyChart"] {{
    background: {CARD_LOW} !important;
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 0.45rem;
    overflow: hidden;
}}

[data-testid="stPlotlyChart"] iframe {{
    background: {CARD_LOW} !important;
    border-radius: 14px;
}}

/* ── Dividers ───────────────────────────────────────────────────────── */

hr {{
    border-color: {BORDER} !important;
    opacity: 0.85;
}}

/* ── Scrollbar ──────────────────────────────────────────────────────── */

::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: {BG_SURFACE};
}}

::-webkit-scrollbar-thumb {{
    background: #686270;
    border-radius: 999px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: {LAV_400};
}}

/* ── Responsive layout ──────────────────────────────────────────────── */

@media (max-width: 768px) {{
    [data-testid="stMainBlockContainer"] {{
        padding: 1rem 1rem 2rem;
    }}

    [data-testid="stMetric"] {{
        border-radius: 16px !important;
        padding: 0.9rem !important;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 1.35rem !important;
    }}

    .sw-card,
    .sw-card-lavender,
    .sw-card-blue,
    .sw-card-pink {{
        padding: 1rem;
        border-radius: 16px;
    }}
}}
</style>
"""


def inject_css():
    """Inject the shared SpendWise theme into the current Streamlit page."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
