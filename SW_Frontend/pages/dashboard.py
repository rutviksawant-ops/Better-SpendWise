"""SpendWise dashboard — presentation only; calculations stay in analytics_engine."""
from __future__ import annotations

import html
import os
import sys
from calendar import month_abbr
from datetime import date, timedelta

_FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND_DIR = os.path.abspath(os.path.join(_FRONTEND_DIR, "..", "SW_Backend"))
for _path in (_FRONTEND_DIR, _BACKEND_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import analytics_engine as ae
import plotly.graph_objects as go
import streamlit as st
import transaction_manager as tm
from theme import (
    ACC_BLUE,
    ACC_MINT,
    ACC_PINK,
    ACC_PURPLE,
    ACC_YELLOW,
    BG_SURFACE,
    BORDER,
    CARD_HIGH,
    CARD_LOW,
    EXPENSE_COLOR,
    INCOME_COLOR,
    LAV_100,
    LAV_200,
    LAV_300,
    LAV_400,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    inject_css,
)

GRID_COLOR = "#524E59"
CHART_COLORS = [
    LAV_300,
    ACC_MINT,
    ACC_PINK,
    ACC_BLUE,
    ACC_YELLOW,
    ACC_PURPLE,
    INCOME_COLOR,
    EXPENSE_COLOR,
    LAV_200,
]
DATE_FMT = "%Y-%m-%d"


def _inject_dashboard_css() -> None:
    """Apply shared SpendWise theme and dashboard-specific dark sticker-book layout rules."""
    inject_css()
    st.markdown(
        f"""
        <style>
        /* Hero banner */
        .sw-dash-hero {{
            background: linear-gradient(135deg, {CARD_HIGH} 0%, #3E3648 100%);
            border: 1.5px solid {BORDER};
            border-radius: 22px;
            padding: 1.35rem 1.6rem;
            margin-bottom: 1.15rem;
            box-shadow: 0 5px 0 rgba(20, 18, 24, 0.28);
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }}
        .sw-dash-eyebrow {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 0.15rem;
            flex-wrap: wrap;
        }}
        .sw-dash-title {{
            color: {TEXT_PRIMARY} !important;
            font-family: "Bricolage Grotesque", sans-serif !important;
            font-size: clamp(1.75rem, 2.6vw, 2.25rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.15;
            margin: 0;
        }}
        .sw-dash-sub {{
            color: {TEXT_SECONDARY} !important;
            font-size: 0.95rem;
            margin: 0;
        }}

        /* Section headers */
        .sw-sec-head {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin: 0.35rem 0 0.85rem 0;
        }}
        .sw-sec-title {{
            font-family: "Bricolage Grotesque", sans-serif !important;
            font-size: 1.25rem;
            font-weight: 800;
            color: {TEXT_PRIMARY} !important;
            letter-spacing: -0.02em;
            margin: 0;
        }}
        .sw-sticker-sm {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.2rem 0.55rem;
            border: 2px solid #231F29;
            border-radius: 10px;
            font-family: "Bricolage Grotesque", sans-serif;
            font-size: 0.82rem;
            font-weight: 800;
            box-shadow: 2px 2px 0 #211D26;
            transform: rotate(-2deg);
        }}

        /* KPI cards */
        .sw-kpi-card {{
            background: {CARD_LOW};
            border: 1.5px solid {BORDER};
            border-radius: 20px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 4px 0 rgba(20, 18, 24, 0.26);
            min-height: 142px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.16s ease, border-color 0.16s ease;
        }}
        .sw-kpi-card:hover {{
            transform: translateY(-2px);
            border-color: {LAV_300};
        }}
        .sw-kpi-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
        }}
        .sw-kpi-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .sw-kpi-icon {{
            width: 32px;
            height: 32px;
            border-radius: 10px;
            border: 1.5px solid #241F2B;
            box-shadow: 2px 2px 0 #211D26;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-family: "Bricolage Grotesque", sans-serif;
            font-weight: 800;
            font-size: 0.92rem;
            flex-shrink: 0;
        }}
        .sw-kpi-val {{
            font-family: "Bricolage Grotesque", sans-serif;
            font-size: clamp(1.35rem, 1.9vw, 1.7rem);
            font-weight: 800;
            color: {TEXT_PRIMARY};
            letter-spacing: -0.025em;
            margin: 0.45rem 0 0.25rem 0;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }}
        .sw-kpi-cap {{
            color: {TEXT_SECONDARY};
            font-size: 0.8rem;
            font-weight: 500;
        }}

        /* At a Glance banner */
        .sw-glance-wrap {{
            background: #443650;
            border: 1.5px solid #71568C;
            border-radius: 20px;
            padding: 1.2rem 1.5rem;
            box-shadow: 0 4px 0 rgba(20, 18, 24, 0.24);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1.2rem;
        }}
        .sw-glance-period {{
            font-family: "Bricolage Grotesque", sans-serif;
            font-size: 1.45rem;
            font-weight: 800;
            color: {TEXT_PRIMARY};
            margin-top: 0.2rem;
        }}
        .sw-glance-metrics {{
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        .sw-glance-stat {{
            background: {BG_SURFACE};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 0.65rem 1.1rem;
            min-width: 145px;
        }}
        .sw-glance-stat-label {{
            color: {TEXT_SECONDARY};
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .sw-glance-stat-val {{
            font-family: "Bricolage Grotesque", sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            color: {LAV_100};
            margin-top: 0.15rem;
        }}

        /* Recent Transactions rows */
        .sw-tx-row {{
            background: {CARD_LOW};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 0.85rem 1.15rem;
            margin-bottom: 0.6rem;
            box-shadow: 0 3px 0 rgba(20, 18, 24, 0.20);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            transition: border-color 0.15s ease, transform 0.15s ease;
        }}
        .sw-tx-row:hover {{
            border-color: {LAV_400};
            transform: translateY(-1px);
        }}
        .sw-tx-left {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            min-width: 0;
        }}
        .sw-tx-dot {{
            width: 36px;
            height: 36px;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.85rem;
            flex-shrink: 0;
        }}
        .sw-tx-cat {{
            font-family: "Bricolage Grotesque", sans-serif;
            font-weight: 700;
            font-size: 0.98rem;
            color: {TEXT_PRIMARY};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .sw-tx-meta {{
            color: {TEXT_SECONDARY};
            font-size: 0.81rem;
            margin-top: 0.1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .sw-tx-right {{
            text-align: right;
            flex-shrink: 0;
        }}

        /* ===== Compact sticker-book dashboard ===== */

        /* Tighten the overall page */
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 1440px !important;
        }}

        div[data-testid="stVerticalBlock"] {{
            gap: 0.65rem;
        }}

        div[data-testid="stHorizontalBlock"] {{
            gap: 0.8rem;
        }}

        /* Hero: bolder sticker outline, less padding */
        .sw-dash-hero {{
            border: 3px solid #211D26 !important;
            border-radius: 18px !important;
            padding: 0.95rem 1.2rem !important;
            margin-bottom: 0.25rem !important;
            box-shadow: 4px 4px 0 #211D26 !important;
            background: linear-gradient(135deg, #514064 0%, #393044 100%) !important;
            gap: 0.25rem !important;
        }}

        .sw-dash-title {{
            font-size: clamp(1.6rem, 2.2vw, 2rem) !important;
        }}

        .sw-dash-sub {{
            font-size: 0.88rem !important;
        }}

        /* Section headings: tighter spacing */
        .sw-sec-head {{
            margin: 0.15rem 0 0.45rem !important;
            gap: 0.55rem !important;
        }}

        .sw-sec-title {{
            font-size: 1.12rem !important;
        }}

        .sw-sticker-sm {{
            border: 2px solid #211D26 !important;
            box-shadow: 3px 3px 0 #211D26 !important;
        }}

        /* KPI cards: purple fills + thick sticker outlines */
        .sw-kpi-card {{
            background: linear-gradient(145deg, #514064 0%, #40334F 100%) !important;
            border: 3px solid #211D26 !important;
            border-radius: 17px !important;
            padding: 0.8rem 0.9rem !important;
            min-height: 118px !important;
            box-shadow: 4px 4px 0 #211D26 !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }}

        .sw-kpi-card:hover {{
            transform: translate(-1px, -2px) !important;
            box-shadow: 5px 6px 0 #211D26 !important;
            border-color: #211D26 !important;
        }}

        .sw-kpi-label {{
            color: #E9DDF8 !important;
            font-size: 0.7rem !important;
            letter-spacing: 0.055em !important;
        }}

        .sw-kpi-icon {{
            border: 2px solid #211D26 !important;
            box-shadow: 2px 2px 0 #211D26 !important;
            width: 29px !important;
            height: 29px !important;
            border-radius: 9px !important;
        }}

        .sw-kpi-val {{
            color: #FFFFFF !important;
            font-size: clamp(1.2rem, 1.65vw, 1.55rem) !important;
            margin: 0.3rem 0 0.15rem !important;
        }}

        .sw-kpi-cap {{
            color: #D2C5E2 !important;
            font-size: 0.75rem !important;
        }}

        /* Remove the old thin accent-top treatment; use a full sticker border */
        .sw-kpi-card[style] {{
            border: 3px solid #211D26 !important;
        }}

        /* At a Glance: deeper purple panel */
        .sw-glance-wrap {{
            background: linear-gradient(135deg, #58436F 0%, #443451 100%) !important;
            border: 3px solid #211D26 !important;
            border-radius: 17px !important;
            padding: 0.85rem 1.05rem !important;
            gap: 0.8rem !important;
            box-shadow: 4px 4px 0 #211D26 !important;
        }}

        .sw-glance-period {{
            font-size: 1.25rem !important;
        }}

        .sw-glance-metrics {{
            gap: 0.65rem !important;
        }}

        .sw-glance-stat {{
            background: #352A40 !important;
            border: 2px solid #211D26 !important;
            border-radius: 12px !important;
            padding: 0.5rem 0.75rem !important;
            min-width: 125px !important;
            box-shadow: 2px 2px 0 #211D26 !important;
        }}

        .sw-glance-stat-label {{
            font-size: 0.68rem !important;
        }}

        .sw-glance-stat-val {{
            font-size: 1.08rem !important;
        }}

        /* Recent transactions: compact purple sticker rows */
        .sw-tx-row {{
            background: #453653 !important;
            border: 2.5px solid #211D26 !important;
            border-radius: 13px !important;
            padding: 0.55rem 0.8rem !important;
            margin-bottom: 0.4rem !important;
            box-shadow: 3px 3px 0 #211D26 !important;
        }}

        .sw-tx-row:hover {{
            border-color: #211D26 !important;
            transform: translate(-1px, -1px) !important;
            box-shadow: 4px 4px 0 #211D26 !important;
        }}

        .sw-tx-left {{
            gap: 0.65rem !important;
        }}

        .sw-tx-dot {{
            width: 31px !important;
            height: 31px !important;
            border: 2px solid #211D26 !important;
            border-radius: 9px !important;
        }}

        .sw-tx-cat {{
            font-size: 0.9rem !important;
        }}

        .sw-tx-meta {{
            font-size: 0.75rem !important;
        }}

        /* Smaller divider spacing */
        div[data-testid="stDivider"] {{
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }}

        /* Compact chart areas */
        div[data-testid="stPlotlyChart"] {{
            margin-top: -0.15rem !important;
            margin-bottom: -0.35rem !important;
        }}

        /* Keep the purple card palette consistent across chart surfaces */
        div[data-testid="stPlotlyChart"] > div {{
            border-radius: 13px;
        }}

        /* Compact captions and period controls */
        div[data-testid="stCaptionContainer"] {{
            margin-top: -0.2rem !important;
        }}

        div[data-testid="stSelectbox"] {{
            margin-bottom: 0 !important;
        }}

        /* Smaller screens: prevent cards from feeling cramped */
        @media (max-width: 900px) {{
            .sw-kpi-card {{
                padding: 0.7rem !important;
                min-height: 108px !important;
            }}

            .sw-kpi-val {{
                font-size: 1.15rem !important;
            }}

            .sw-glance-wrap {{
                align-items: flex-start !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _fmt(amount: float) -> str:
    return f"₹ {amount:,.2f}"


def _fmt_compact(amount: float) -> str:
    sign = "−" if amount < 0 else ""
    value = abs(amount)
    if value >= 10_000_000:
        return f"{sign}₹{value / 10_000_000:.2f}Cr"
    if value >= 100_000:
        return f"{sign}₹{value / 100_000:.2f}L"
    if value >= 1_000:
        return f"{sign}₹{value / 1_000:.1f}K"
    return f"{sign}₹{value:,.0f}"


def _fmt_month(month: str) -> str:
    try:
        year, number = month.split("-")
        return f"{month_abbr[int(number)]} {year[2:]}"
    except (ValueError, IndexError, TypeError):
        return month


def _plotly_layout(title: str = "", **overrides) -> dict:
    layout = {
        "title": {
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "family": "Bricolage Grotesque, Figtree, sans-serif",
                "color": TEXT_PRIMARY,
                "size": 16,
            },
        },
        "paper_bgcolor": CARD_LOW,
        "plot_bgcolor": CARD_LOW,
        "font": {"family": "Figtree, sans-serif", "color": TEXT_PRIMARY, "size": 12},
        "legend": {
            "font": {"color": TEXT_SECONDARY, "size": 11},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
        },
        "margin": {"l": 20, "r": 24, "t": 56, "b": 34},
        "hoverlabel": {
            "bgcolor": BG_SURFACE,
            "bordercolor": LAV_300,
            "font": {"family": "Figtree, sans-serif", "color": TEXT_PRIMARY, "size": 12},
        },
        "autosize": True,
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(layout.get(key), dict):
            layout[key] = {**layout[key], **value}
        else:
            layout[key] = value
    return layout


def _axis_style(**overrides) -> dict:
    axis = {
        "showgrid": True,
        "gridcolor": GRID_COLOR,
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
        "tickfont": {"family": "Figtree, sans-serif", "color": TEXT_SECONDARY, "size": 11},
        "automargin": True,
    }
    axis.update(overrides)
    return axis


def _chart_config() -> dict:
    return {"displayModeBar": False, "responsive": True, "scrollZoom": False}


def _section_heading(title: str, sticker: str = "✳", bg_color: str = LAV_200, fg_color: str = "#292033") -> None:
    st.markdown(
        f"""
        <div class="sw-sec-head">
            <span class="sw-sticker-sm" style="background:{bg_color};color:{fg_color};">{sticker}</span>
            <h3 class="sw-sec-title">{html.escape(title)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _show_chart(fig, height: int | None = None) -> None:
    if height is not None:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, config=_chart_config())


def _period_selector() -> tuple[str | None, str | None, str]:
    today = date.today()
    choice = st.selectbox(
        "Period",
        [
            "This Month",
            "Last 30 Days",
            "Last 3 Months",
            "Last 6 Months",
            "This Year",
            "All Time",
            "Custom Range",
        ],
        key="dash_period",
        label_visibility="collapsed",
    )
    if choice == "This Month":
        start, end, label = date(today.year, today.month, 1), today, today.strftime("%B %Y")
    elif choice == "Last 30 Days":
        start, end, label = today - timedelta(days=29), today, "Last 30 Days"
    elif choice == "Last 3 Months":
        start, end, label = today - timedelta(days=90), today, "Last 3 Months"
    elif choice == "Last 6 Months":
        start, end, label = today - timedelta(days=180), today, "Last 6 Months"
    elif choice == "This Year":
        start, end, label = date(today.year, 1, 1), today, str(today.year)
    elif choice == "All Time":
        return None, None, "All Time"
    else:
        col_s, col_e = st.columns(2)
        with col_s:
            start = st.date_input("From", value=date(today.year, today.month, 1), key="dash_custom_start")
        with col_e:
            end = st.date_input("To", value=today, key="dash_custom_end")
        label = f"{start} → {end}"
    if start > end:
        st.warning("Start date is after end date; the range has been reversed.")
        start, end = end, start
        label = f"{start} → {end}"
    return start.strftime(DATE_FMT), end.strftime(DATE_FMT), label


def _kpi_row(summary: dict) -> None:
    net = summary.get("net", 0)
    savings_rate = summary.get("savings_rate")
    cards = [
        (
            "TOTAL INCOME",
            _fmt(summary.get("total_income", 0)),
            "↗",
            "Money received",
            ACC_MINT,
            "#1F382E",
        ),
        (
            "TOTAL EXPENSES",
            _fmt(summary.get("total_expense", 0)),
            "↘",
            "Money spent",
            ACC_PINK,
            "#382330",
        ),
        (
            "NET BALANCE",
            ("−" if net < 0 else "") + _fmt(abs(net)),
            "✳",
            "Surplus" if net >= 0 else "Deficit",
            LAV_200,
            "#292033",
        ),
        (
            "SAVINGS RATE",
            "—" if savings_rate is None else f"{savings_rate:.1f}%",
            "%",
            "No income recorded" if savings_rate is None else "Of recorded income",
            ACC_YELLOW,
            "#38301E",
        ),
    ]
    columns = st.columns(4, gap="medium")
    for column, (label, value, symbol, caption, badge_bg, badge_fg) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="sw-kpi-card">
                    <div class="sw-kpi-top">
                        <span class="sw-kpi-label">{html.escape(label)}</span>
                        <span class="sw-kpi-icon" style="background:{badge_bg};color:{badge_fg};">{symbol}</span>
                    </div>
                    <div class="sw-kpi-val">{html.escape(value)}</div>
                    <div class="sw-kpi-cap">{html.escape(caption)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _at_a_glance(period_label: str, filtered: list, summary: dict) -> None:
    net = summary.get("net", 0)
    result_label = "Surplus" if net > 0 else "Deficit" if net < 0 else "Balanced"
    net_color = INCOME_COLOR if net > 0 else EXPENSE_COLOR if net < 0 else LAV_100
    st.markdown(
        f"""
        <div class="sw-glance-wrap">
            <div>
                <div class="sw-section-label">✳ SELECTED PERIOD</div>
                <div class="sw-glance-period">{html.escape(period_label)}</div>
            </div>
            <div class="sw-glance-metrics">
                <div class="sw-glance-stat">
                    <div class="sw-glance-stat-label">Transactions</div>
                    <div class="sw-glance-stat-val">{len(filtered)}</div>
                </div>
                <div class="sw-glance-stat">
                    <div class="sw-glance-stat-label">{result_label}</div>
                    <div class="sw-glance-stat-val" style="color:{net_color};">{html.escape(_fmt(net))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _recent_transactions(transactions: list, n: int = 6) -> None:
    recent = ae.recent_transactions(transactions, n)
    _section_heading("Recent Transactions", "↻", bg_color=ACC_BLUE, fg_color="#222A36")
    if not recent:
        st.info("No transactions in this period.", icon="ℹ️")
        return
    for tx in recent:
        is_income = tx.get("type") == "income"
        badge_class = "sw-badge-income" if is_income else "sw-badge-expense"
        dot_bg = "#244638" if is_income else "#4D3039"
        dot_fg = INCOME_COLOR if is_income else EXPENSE_COLOR
        sign = "▲" if is_income else "▼"

        category = html.escape(str(tx.get("category", "Uncategorised")))
        details = str(tx.get("date", ""))
        if tx.get("note"):
            details += f" · {tx['note']}"
        details_escaped = html.escape(details)
        amount = html.escape(_fmt(float(tx.get("amount", 0))))

        st.markdown(
            f"""
            <div class="sw-tx-row">
                <div class="sw-tx-left">
                    <div class="sw-tx-dot" style="background:{dot_bg};color:{dot_fg};">
                        {sign}
                    </div>
                    <div style="min-width:0;">
                        <div class="sw-tx-cat">{category}</div>
                        <div class="sw-tx-meta">{details_escaped}</div>
                    </div>
                </div>
                <div class="sw-tx-right">
                    <span class="{badge_class}">{sign} {amount}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _category_chart(transactions: list, start_date: str | None, end_date: str | None) -> None:
    breakdown = ae.category_breakdown(transactions, "expense", start_date, end_date)
    _section_heading("Spending Breakdown", "✦", bg_color=ACC_PINK, fg_color="#382533")
    if not breakdown:
        st.info("No expense data for the selected period.", icon="ℹ️")
        return
    ranked = sorted(breakdown.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in ranked]
    values = [item[1] for item in ranked]
    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
    total = sum(values)

    left, right = st.columns([1, 1.15], gap="large")
    with left:
        pie = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                sort=False,
                direction="clockwise",
                marker={"colors": colors, "line": {"color": CARD_LOW, "width": 2.5}},
                textinfo="percent",
                textposition="inside",
                textfont={"family": "Figtree, sans-serif", "color": "#231F29", "size": 11},
                hovertemplate="<b>%{label}</b><br>Spent: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
            )
        )
        pie.update_layout(
            **_plotly_layout(
                "Where your money went",
                height=320,
                margin={"l": 12, "r": 12, "t": 56, "b": 42},
                legend={
                    "orientation": "h",
                    "x": 0.5,
                    "xanchor": "center",
                    "y": -0.04,
                    "yanchor": "top",
                    "font": {"color": TEXT_SECONDARY, "size": 11},
                },
                annotations=[
                    {
                        "x": 0.5,
                        "y": 0.5,
                        "xref": "paper",
                        "yref": "paper",
                        "text": (
                            f"<span style='font-size:10px;color:{TEXT_SECONDARY}'>TOTAL SPENT</span>"
                            f"<br><b style='color:{TEXT_PRIMARY}'>{_fmt_compact(total)}</b>"
                        ),
                        "showarrow": False,
                        "align": "center",
                        "font": {
                            "family": "Bricolage Grotesque, sans-serif",
                            "color": TEXT_PRIMARY,
                            "size": 16,
                        },
                    }
                ],
            )
        )
        _show_chart(pie)

    with right:
        bar = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker={"color": colors, "line": {"width": 0}},
                text=[_fmt_compact(v) for v in values],
                textposition="outside",
                cliponaxis=False,
                textfont={"family": "Figtree, sans-serif", "color": TEXT_PRIMARY, "size": 11},
                hovertemplate="<b>%{y}</b><br>Spent: ₹%{x:,.2f}<extra></extra>",
            )
        )
        bar.update_layout(
            **_plotly_layout(
                "Spending by Category",
                height=max(320, min(460, len(labels) * 32 + 85)),
                margin={"l": 14, "r": 68, "t": 56, "b": 34},
                showlegend=False,
                xaxis=_axis_style(
                    tickprefix="₹",
                    tickformat="~s",
                    range=[0, max(values) * 1.38 if max(values) else 1],
                    title=None,
                ),
                yaxis=_axis_style(
                    showgrid=False,
                    autorange="reversed",
                    title=None,
                    tickfont={"family": "Figtree, sans-serif", "color": TEXT_PRIMARY, "size": 12},
                ),
            )
        )
        _show_chart(bar)


def _monthly_trend_chart(transactions: list) -> None:
    data = ae.income_vs_expense_monthly(transactions)
    if not data:
        st.info("Not enough dated data for a monthly trend chart.", icon="ℹ️")
        return
    months = [row["month"] for row in data]
    xlabels = [_fmt_month(month) for month in months]
    incomes = [row["income"] for row in data]
    expenses = [row["expense"] for row in data]

    def label_indices(values: list, limit: int = 8) -> set[int]:
        if len(values) <= limit:
            return set(range(len(values)))
        return {
            len(values) - 1,
            max(range(len(values)), key=lambda i: values[i]),
            min(range(len(values)), key=lambda i: values[i]),
        }

    income_ids, expense_ids = label_indices(incomes), label_indices(expenses)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Income",
            x=xlabels,
            y=incomes,
            marker={"color": INCOME_COLOR, "line": {"width": 0}},
            text=[_fmt_compact(v) if i in income_ids else "" for i, v in enumerate(incomes)],
            textposition="outside",
            cliponaxis=False,
            textfont={"color": TEXT_PRIMARY, "size": 10},
            hovertemplate="<b>%{x}</b><br>Income: ₹%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Expenses",
            x=xlabels,
            y=expenses,
            marker={"color": EXPENSE_COLOR, "line": {"width": 0}},
            text=[_fmt_compact(v) if i in expense_ids else "" for i, v in enumerate(expenses)],
            textposition="outside",
            cliponaxis=False,
            textfont={"color": TEXT_PRIMARY, "size": 10},
            hovertemplate="<b>%{x}</b><br>Expenses: ₹%{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_plotly_layout(
            "Monthly Income vs Expenses",
            barmode="group",
            bargap=0.32,
            bargroupgap=0.12,
            height=350,
            margin={"l": 24, "r": 28, "t": 72, "b": 56},
            hovermode="x unified",
            xaxis=_axis_style(
                showgrid=False,
                type="category",
                tickangle=-30 if len(xlabels) > 6 else 0,
                title=None,
            ),
            yaxis=_axis_style(
                tickprefix="₹",
                tickformat="~s",
                separatethousands=True,
                rangemode="tozero",
                title=None,
            ),
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
                "title_text": "",
                "font": {"color": TEXT_PRIMARY, "size": 11},
            },
        )
    )
    _show_chart(fig)


def render() -> None:
    _inject_dashboard_css()

    top_left, top_right = st.columns([3.2, 1.8], gap="medium", vertical_alignment="center")
    with top_left:
        st.markdown(
            """
            <div class="sw-dash-hero">
                <div class="sw-dash-eyebrow">
                    <span class="sw-sticker">SpendWise</span>
                    <span class="sw-section-label">Financial Overview</span>
                </div>
                <div class="sw-dash-title">Your money, your picture.</div>
                <div class="sw-dash-sub">A clearer view of where your money goes.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        st.markdown('<div class="sw-section-label" style="margin-bottom:0.35rem;">📅 TIMEFRAME</div>', unsafe_allow_html=True)
        start_date, end_date, period_label = _period_selector()
        st.caption(f"Showing data for: **{period_label}**")

    try:
        all_transactions = tm.get_transactions()
    except Exception as exc:
        st.error(f"Could not load transactions: {exc}", icon="❌")
        return

    filtered = [
        tx
        for tx in all_transactions
        if (start_date is None or tx.get("date", "") >= start_date)
        and (end_date is None or tx.get("date", "") <= end_date)
    ]
    if not all_transactions:
        st.info("No transactions yet. Head to **💳 Transactions** to add some.", icon="ℹ️")
        return

    summary = ae.summary(all_transactions, start_date, end_date)
    _kpi_row(summary)
    st.divider()
    _section_heading("At a Glance", "✳", bg_color=LAV_200, fg_color="#292033")
    _at_a_glance(period_label, filtered, summary)
    st.divider()
    _category_chart(all_transactions, start_date, end_date)
    st.divider()
    _section_heading("Monthly Trend", "↗", bg_color=ACC_MINT, fg_color="#203B30")
    _monthly_trend_chart(all_transactions)
    st.divider()
    _recent_transactions(filtered, n=6)
    st.caption("ℹ️ Net Balance reflects income minus expenses for the selected period — not your actual bank balance.")