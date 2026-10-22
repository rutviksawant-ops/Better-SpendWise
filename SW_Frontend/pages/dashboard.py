"""
pages/dashboard.py
==================
Dashboard page for SpendWise.

Pulls real transactions from transaction_manager, runs analytics_engine
calculations, and presents:
  - Period selector (current month / last 30 days / custom)
  - Headline KPIs: income, expense, net, savings rate
  - Recent transactions list
  - Expense breakdown by category (Plotly pie + bar)
  - Monthly income vs expense comparison (Plotly bar)
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

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import date, timedelta
from calendar import month_abbr

from theme import (
    LAV_100, LAV_200, LAV_300, LAV_400, LAV_500,
    TEXT_PRIMARY, TEXT_SECONDARY,
    CARD_LOW, BORDER, BG_DEEP,
    INCOME_COLOR, EXPENSE_COLOR,
    ACC_BLUE, ACC_PINK, ACC_PURPLE,
)

DATE_FMT = "%Y-%m-%d"

# Plotly colour sequence using our palette
_PLOTLY_COLORS = [LAV_300, ACC_BLUE, ACC_PINK, LAV_500, ACC_PURPLE,
                  LAV_200, LAV_400, "#6EE7B7", "#F87171", "#FCD34D"]


def _plotly_layout(title: str = "", **overrides) -> dict:
    """
    Shared Plotly layout overrides for the dark theme.

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
        margin=dict(l=10, r=10, t=40, b=10),
    )
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(layout.get(key), dict):
            layout[key] = {**layout[key], **value}
        else:
            layout[key] = value
    return layout


def _fmt(amount: float) -> str:
    return f"₹ {amount:,.2f}"


# ---------------------------------------------------------------------------
# Period selector
# ---------------------------------------------------------------------------
def _period_selector() -> tuple[str | None, str | None, str]:
    """
    Render a period picker and return (start_date_str, end_date_str, label).
    Both dates are YYYY-MM-DD strings (or None for 'all time').
    """
    today = date.today()
    options = [
        "This Month",
        "Last 30 Days",
        "Last 3 Months",
        "Last 6 Months",
        "This Year",
        "All Time",
        "Custom Range",
    ]
    choice = st.selectbox("Period", options=options, key="dash_period",
                          label_visibility="collapsed")

    if choice == "This Month":
        start = date(today.year, today.month, 1)
        end   = today
        label = f"{today.strftime('%B %Y')}"
    elif choice == "Last 30 Days":
        start = today - timedelta(days=30)
        end   = today
        label = "Last 30 Days"
    elif choice == "Last 3 Months":
        start = today - timedelta(days=90)
        end   = today
        label = "Last 3 Months"
    elif choice == "Last 6 Months":
        start = today - timedelta(days=180)
        end   = today
        label = "Last 6 Months"
    elif choice == "This Year":
        start = date(today.year, 1, 1)
        end   = today
        label = str(today.year)
    elif choice == "All Time":
        return None, None, "All Time"
    else:  # Custom Range
        col_s, col_e = st.columns(2)
        with col_s:
            start = st.date_input("From", value=date(today.year, today.month, 1),
                                  key="dash_custom_start")
        with col_e:
            end = st.date_input("To", value=today, key="dash_custom_end")
        label = f"{start} → {end}"

    return start.strftime(DATE_FMT), end.strftime(DATE_FMT), label


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
def _kpi_row(s: dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("▲ Income",   _fmt(s["total_income"]))
    c2.metric("▼ Expenses", _fmt(s["total_expense"]))
    net = s["net"]
    c3.metric(
        "💰 Net Balance",
        _fmt(abs(net)),
        delta=f"{'▲ surplus' if net >= 0 else '▼ deficit'}",
        delta_color="normal" if net >= 0 else "inverse",
    )
    sr = s["savings_rate"]
    if sr is None:
        c4.metric("💼 Savings Rate", "—", help="No income recorded in this period.")
    else:
        c4.metric("💼 Savings Rate", f"{sr:.1f}%",
                  delta_color="normal" if sr >= 0 else "inverse")


# ---------------------------------------------------------------------------
# Recent transactions
# ---------------------------------------------------------------------------
def _recent_transactions(transactions: list, n: int = 5):
    recent = ae.recent_transactions(transactions, n)
    if not recent:
        st.info("No transactions in this period.", icon="ℹ️")
        return

    st.markdown(
        f"<h4 style='color:{LAV_200}; margin:0.5rem 0;'>🕐 Recent Transactions</h4>",
        unsafe_allow_html=True,
    )
    for t in recent:
        color = INCOME_COLOR if t.get("type") == "income" else EXPENSE_COLOR
        sign  = "▲" if t.get("type") == "income" else "▼"
        note_html = f" — {t['note']}" if t.get("note") else ""
        st.markdown(
            f"""
            <div style="
                background:{CARD_LOW}; border:1px solid {BORDER}; border-radius:8px;
                padding:0.55rem 1rem; margin-bottom:0.4rem;
                display:flex; justify-content:space-between; align-items:center;
            ">
                <span>
                    <span style="color:{TEXT_SECONDARY}; font-size:0.8rem;">
                        {t['date']} &nbsp;·&nbsp; {t['category']}
                    </span>
                    <span style="color:{TEXT_SECONDARY}; font-size:0.75rem;">{note_html}</span>
                </span>
                <span style="color:{color}; font-weight:700; font-size:1rem;">
                    {sign} {_fmt(t['amount'])}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Category breakdown chart
# ---------------------------------------------------------------------------
def _category_chart(transactions: list, start_date, end_date):
    cb = ae.category_breakdown(transactions, "expense", start_date, end_date)
    if not cb:
        st.info("No expense data for the selected period.", icon="ℹ️")
        return

    labels  = list(cb.keys())
    values  = list(cb.values())
    colors  = _PLOTLY_COLORS[:len(labels)]

    col_pie, col_bar = st.columns(2)

    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker=dict(colors=colors, line=dict(color=BG_DEEP, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.2f}<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(**_plotly_layout("Expense by Category"))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        fig_bar = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.2f}<extra></extra>",
            text=[f"₹{v:,.0f}" for v in values],
            textposition="outside",
            textfont=dict(color=TEXT_SECONDARY),
        ))
        fig_bar.update_layout(
            **_plotly_layout(""),
            xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ---------------------------------------------------------------------------
# Monthly income vs expense trend
# ---------------------------------------------------------------------------
def _monthly_trend_chart(transactions: list):
    ive = ae.income_vs_expense_monthly(transactions)
    if len(ive) < 1:
        st.info("Not enough dated data for a monthly trend chart.", icon="ℹ️")
        return

    months  = [row["month"] for row in ive]
    incomes  = [row["income"]  for row in ive]
    expenses = [row["expense"] for row in ive]

    # Prettier month labels: "2026-10" → "Oct 26"
    def fmt_month(m: str) -> str:
        try:
            y, mo = m.split("-")
            return f"{month_abbr[int(mo)]} {y[2:]}"
        except Exception:
            return m

    xlabels = [fmt_month(m) for m in months]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Income",
        x=xlabels, y=incomes,
        marker_color=INCOME_COLOR,
        hovertemplate="Income<br>₹%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Expenses",
        x=xlabels, y=expenses,
        marker_color=EXPENSE_COLOR,
        hovertemplate="Expenses<br>₹%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(**_plotly_layout(
        "Monthly Income vs Expenses",
        barmode="group",
        xaxis=dict(gridcolor=BORDER),
        yaxis=dict(gridcolor=BORDER, tickprefix="₹"),
        legend=dict(orientation="h", y=1.1),
    ))
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render():
    st.markdown(
        f"<h1 style='color:{LAV_100}; margin-bottom:0.1rem;'>📊 Dashboard</h1>",
        unsafe_allow_html=True,
    )

    # Period selector
    pcol, _ = st.columns([2, 6])
    with pcol:
        start_date, end_date, period_label = _period_selector()

    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin:0 0 1.2rem;'>"
        f"Showing data for: <strong style='color:{LAV_300};'>{period_label}</strong></p>",
        unsafe_allow_html=True,
    )

    # Load transactions — read-only
    try:
        all_transactions = tm.get_transactions()
    except Exception as exc:
        st.error(f"Could not load transactions: {exc}", icon="❌")
        return

    # Period-filtered for summary / charts
    filtered = [
        t for t in all_transactions
        if (start_date is None or t.get("date", "") >= start_date)
        and (end_date is None or t.get("date", "") <= end_date)
    ]

    if not all_transactions:
        st.info(
            "No transactions yet. Head to **💳 Transactions** to add some.",
            icon="ℹ️",
        )
        return

    # ── KPIs ──────────────────────────────────────────────────────────────
    s = ae.summary(all_transactions, start_date, end_date)
    _kpi_row(s)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Recent transactions + category chart side by side ─────────────────
    col_recent, col_chart = st.columns([2, 3])
    with col_recent:
        _recent_transactions(filtered, n=6)

    with col_chart:
        st.markdown(
            f"<h4 style='color:{LAV_200}; margin:0.5rem 0;'>📂 Expense Breakdown</h4>",
            unsafe_allow_html=True,
        )
        _category_chart(all_transactions, start_date, end_date)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Monthly trend (uses all transactions, not period-filtered) ────────
    st.markdown(
        f"<h4 style='color:{LAV_200}; margin:0.5rem 0;'>📅 Monthly Income vs Expenses</h4>",
        unsafe_allow_html=True,
    )
    _monthly_trend_chart(all_transactions)

    # ── Footer note ───────────────────────────────────────────────────────
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; font-size:0.75rem; margin-top:1rem;'>"
        f"ℹ️  Net Balance reflects income minus expenses for the selected period — "
        f"not your actual bank balance.</p>",
        unsafe_allow_html=True,
    )
