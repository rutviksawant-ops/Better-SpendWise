"""
pages/analytics.py
==================
Analytics page for SpendWise.

Sections:
  1. Expense Distribution by Category (pie + sorted bar)
  2. Monthly Expense Trend (line chart)
  3. Income vs Expense Comparison (grouped bar)
  4. Unusual Spending Alerts (rule-based, explainable)

All calculations delegate to analytics_engine — no logic here.
"""

from __future__ import annotations

import sys
import os

_BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "SW_Backend")
)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import transaction_manager as tm
import analytics_engine as ae

import plotly.graph_objects as go
import streamlit as st
from calendar import month_abbr
from datetime import date

from theme import (
    LAV_100, LAV_200, LAV_300, LAV_400, LAV_500,
    TEXT_PRIMARY, TEXT_SECONDARY,
    CARD_LOW, BORDER, BG_DEEP,
    INCOME_COLOR, EXPENSE_COLOR,
    ACC_BLUE, ACC_PINK, ACC_PURPLE,
)

_PLOTLY_COLORS = [LAV_300, ACC_BLUE, ACC_PINK, LAV_500, ACC_PURPLE,
                  LAV_200, LAV_400, "#6EE7B7", "#F87171", "#FCD34D"]

DATE_FMT = "%Y-%m-%d"


def _plotly_layout(title: str = "", **overrides) -> dict:
    """
    Shared Plotly dark-theme layout.

    Extra keyword arguments (e.g. legend=dict(orientation="h"), xaxis=...)
    are merged into the defaults, so a key is never passed to
    fig.update_layout() twice. Dict values are merged one level deep.
    """
    layout = dict(
        title=dict(text=title, font=dict(color=LAV_200, size=15)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_PRIMARY),
        legend=dict(font=dict(color=TEXT_SECONDARY)),
        margin=dict(l=10, r=10, t=45, b=10),
    )
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(layout.get(key), dict):
            layout[key] = {**layout[key], **value}
        else:
            layout[key] = value
    return layout


def _fmt_month(m: str) -> str:
    try:
        y, mo = m.split("-")
        return f"{month_abbr[int(mo)]} {y[2:]}"
    except Exception:
        return m


def _fmt(amount: float) -> str:
    return f"₹ {amount:,.2f}"


# ---------------------------------------------------------------------------
# Alert settings sidebar / expander
# ---------------------------------------------------------------------------
def _alert_settings() -> tuple[float, float]:
    with st.expander("⚙️  Alert Settings", expanded=False):
        st.markdown(
            f"<p style='color:{TEXT_SECONDARY}; font-size:0.85rem;'>"
            f"Alerts use two transparent rules:<br>"
            f"<strong>Rule 1</strong> — A single expense above the absolute threshold.<br>"
            f"<strong>Rule 2</strong> — A single expense ≥ N× the historical category average "
            f"(needs at least 3 past transactions in that category).</p>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            abs_thresh = st.number_input(
                "Absolute threshold (₹)",
                min_value=0.0,
                value=5000.0,
                step=500.0,
                format="%.2f",
                key="alert_abs_thresh",
                help="Flag any single expense above this amount.",
            )
        with col2:
            rel_mult = st.number_input(
                "Relative multiplier (×avg)",
                min_value=1.0,
                value=2.5,
                step=0.5,
                format="%.1f",
                key="alert_rel_mult",
                help="Flag transactions ≥ this multiple of the category average.",
            )
    return abs_thresh, rel_mult


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------
def _section_category_distribution(transactions: list):
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.4rem;'>📂 Expense Distribution by Category</h3>",
        unsafe_allow_html=True,
    )

    cb = ae.category_breakdown(transactions, "expense")
    if not cb:
        st.info("No expense data yet.", icon="ℹ️")
        return

    labels = list(cb.keys())
    values = list(cb.values())
    colors = _PLOTLY_COLORS[:len(labels)]

    col_pie, col_bar = st.columns([2, 3])

    with col_pie:
        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.42,
            marker=dict(colors=colors, line=dict(color=BG_DEEP, width=2)),
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.2f} · %{percent}<extra></extra>",
        ))
        fig.update_layout(**_plotly_layout(""))
        st.plotly_chart(fig, use_container_width=True)

    with col_bar:
        fig2 = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.2f}<extra></extra>",
            text=[f"₹{v:,.0f}" for v in values],
            textposition="outside",
            textfont=dict(color=TEXT_SECONDARY, size=11),
        ))
        fig2.update_layout(
            **_plotly_layout("Amount Spent by Category"),
            xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig2, use_container_width=True)


def _section_monthly_expense_trend(transactions: list):
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.4rem;'>📈 Monthly Expense Trend</h3>",
        unsafe_allow_html=True,
    )

    mt = ae.monthly_trend(transactions, "expense")
    if not mt:
        st.info("No expense data to plot.", icon="ℹ️")
        return
    if len(mt) == 1:
        st.info(
            f"Only one month of data ({_fmt_month(mt[0]['month'])}). "
            f"Add transactions from more months to see a trend.",
            icon="ℹ️",
        )

    xlabels = [_fmt_month(r["month"]) for r in mt]
    values  = [r["amount"] for r in mt]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xlabels, y=values,
        mode="lines+markers",
        name="Expenses",
        line=dict(color=EXPENSE_COLOR, width=2.5),
        marker=dict(size=8, color=EXPENSE_COLOR),
        fill="tozeroy",
        fillcolor=f"{EXPENSE_COLOR}22",
        hovertemplate="<b>%{x}</b><br>₹%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_plotly_layout("Monthly Total Expenses"),
        xaxis=dict(gridcolor=BORDER),
        yaxis=dict(gridcolor=BORDER, tickprefix="₹"),
    )
    st.plotly_chart(fig, use_container_width=True)



def _section_income_vs_expense(transactions: list):
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.4rem;'>💹 Income vs Expense by Month</h3>",
        unsafe_allow_html=True,
    )

    ive = ae.income_vs_expense_monthly(transactions)
    if not ive:
        st.info("No data available.", icon="ℹ️")
        return

    xlabels = [_fmt_month(r["month"]) for r in ive]
    incomes = [r["income"] for r in ive]
    expenses = [r["expense"] for r in ive]
    nets = [r["net"] for r in ive]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Income",
        x=xlabels,
        y=incomes,
        marker_color=INCOME_COLOR,
        hovertemplate="Income: ₹%{y:,.2f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Expenses",
        x=xlabels,
        y=expenses,
        marker_color=EXPENSE_COLOR,
        hovertemplate="Expenses: ₹%{y:,.2f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        name="Net",
        x=xlabels,
        y=nets,
        mode="lines+markers",
        line=dict(color=LAV_300, width=2, dash="dot"),
        marker=dict(size=7, color=LAV_300),
        hovertemplate="Net: ₹%{y:,.2f}<extra></extra>",
        yaxis="y",
    ))

    fig.update_layout(**_plotly_layout(
        "Monthly Income vs Expenses",
        barmode="group",
        height=440,
        margin=dict(l=20, r=20, t=100, b=75),
        xaxis=dict(
            gridcolor=BORDER,
            tickangle=-35,
            automargin=True,
        ),
        yaxis=dict(
            gridcolor=BORDER,
            tickprefix="₹",
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title_text="",
        ),
    ))

    st.plotly_chart(fig, use_container_width=True)



def _section_alerts(transactions: list, abs_thresh: float, rel_mult: float):
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.4rem;'>🔔 Unusual Spending Alerts</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; font-size:0.85rem; margin-top:0;'>"
        f"Each alert is generated by a transparent rule — no machine learning. "
        f"Adjust thresholds in <strong>Alert Settings</strong> above.</p>",
        unsafe_allow_html=True,
    )

    alerts = ae.unusual_spending_alerts(
        transactions,
        abs_threshold=abs_thresh,
        relative_multiplier=rel_mult,
        min_history_count=3,
    )

    if not alerts:
        st.success(
            f"No unusual transactions found with the current thresholds "
            f"(absolute > ₹{abs_thresh:,.0f}, relative > {rel_mult:.1f}× average).",
            icon="✅",
        )
        return

    sev_colors = {"high": EXPENSE_COLOR, "medium": "#FCD34D"}
    rule_labels = {
        "absolute": "Rule 1 · Absolute threshold",
        "relative": "Rule 2 · Above category average",
    }

    for alert in alerts:
        sev   = alert.get("severity", "medium")
        color = sev_colors.get(sev, LAV_400)
        rule  = rule_labels.get(alert.get("rule", "absolute"), "")

        st.markdown(
            f"""
            <div style="background:{CARD_LOW}; border-left:4px solid {color};
                        border-radius:0 8px 8px 0; padding:0.75rem 1rem;
                        margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:{LAV_100}; font-weight:700;">
                        #{alert['tx_id']} · {alert['category']} · {alert['date']}
                    </span>
                    <span style="color:{color}; font-weight:700; font-size:1rem;">
                        ₹{alert['amount']:,.2f}
                    </span>
                </div>
                <div style="color:{TEXT_SECONDARY}; font-size:0.8rem; margin-top:0.3rem;">
                    <strong style="color:{color};">{rule}</strong><br>
                    {alert['reason']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render():
    st.markdown(
        f"<h1 style='color:{LAV_100}; margin-bottom:0.1rem;'>📈 Analytics</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0; margin-bottom:1.2rem;'>"
        f"Insights from your transaction history.</p>",
        unsafe_allow_html=True,
    )

    # Alert settings (collapsed by default)
    abs_thresh, rel_mult = _alert_settings()

    # Load all transactions — read-only
    try:
        transactions = tm.get_transactions()
    except Exception as exc:
        st.error(f"Could not load transactions: {exc}", icon="❌")
        return

    if not transactions:
        st.info(
            "No transactions yet. Head to **💳 Transactions** to add some.",
            icon="ℹ️",
        )
        return

    # Tabs for the four sections
    t1, t2, t3, t4 = st.tabs([
        "📂  Category Distribution",
        "📈  Monthly Trend",
        "💹  Income vs Expense",
        "🔔  Alerts",
    ])

    with t1:
        _section_category_distribution(transactions)

    with t2:
        _section_monthly_expense_trend(transactions)

    with t3:
        _section_income_vs_expense(transactions)

    with t4:
        _section_alerts(transactions, abs_thresh, rel_mult)
