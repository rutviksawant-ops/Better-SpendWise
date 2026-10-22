"""
pages/analytics.py
==================
Analytics page for SpendWise.

Sections:
  1. Expense Distribution by Category (donut + sorted bar)
  2. Monthly Expense Trend (line chart)
  3. Income vs Expense Comparison (grouped bar)
  4. Unusual Spending Alerts (rule-based, explainable)

All calculations delegate to analytics_engine — no logic here.
"""

from __future__ import annotations

from calendar import month_abbr

import backend_bridge
from backend_bridge import tm
import analytics_engine as ae

import plotly.graph_objects as go
import streamlit as st

from theme import (
    LAV_100, LAV_200, LAV_300, LAV_400, LAV_500,
    TEXT_PRIMARY, TEXT_SECONDARY,
    CARD_LOW, CARD_HIGH, BORDER, BG_DEEP,
    INCOME_COLOR, EXPENSE_COLOR,
    ACC_BLUE, ACC_PINK, ACC_PURPLE, ACC_MINT, ACC_YELLOW,
)

# ---------------------------------------------------------------------------
# Graph design system — graphite + bold sticker-book accents
# ---------------------------------------------------------------------------

GRID_COLOR = "#5B5662"
PLOT_BG = CARD_LOW
PAPER_BG = CARD_LOW
OUTLINE = "#29282D"

_PLOTLY_COLORS = [
    LAV_300,
    ACC_BLUE,
    ACC_PINK,
    LAV_500,
    ACC_PURPLE,
    LAV_200,
    LAV_400,
    ACC_MINT,
    EXPENSE_COLOR,
    ACC_YELLOW,
]

DATE_FMT = "%Y-%m-%d"


def _plotly_layout(title: str = "", **overrides) -> dict:
    """Shared dark chart styling."""

    layout = {
        "title": {
            "text": title,
            "x": 0.025,
            "xanchor": "left",
            "font": {
                "family": "Bricolage Grotesque, Figtree, sans-serif",
                "color": TEXT_PRIMARY,
                "size": 19,
            },
        },
        "paper_bgcolor": PAPER_BG,
        "plot_bgcolor": PLOT_BG,
        "font": {
            "family": "Figtree, sans-serif",
            "color": TEXT_PRIMARY,
            "size": 12,
        },
        "legend": {
            "font": {"color": TEXT_PRIMARY, "size": 11},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
        },
        "margin": {"l": 22, "r": 25, "t": 68, "b": 32},
        "hoverlabel": {
            "bgcolor": BG_DEEP,
            "bordercolor": LAV_300,
            "font": {
                "family": "Figtree, sans-serif",
                "color": TEXT_PRIMARY,
                "size": 12,
            },
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
    """Readable axes with restrained gridlines."""

    axis = {
        "showgrid": True,
        "gridcolor": GRID_COLOR,
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
        "tickfont": {
            "family": "Figtree, sans-serif",
            "color": TEXT_SECONDARY,
            "size": 11,
        },
        "automargin": True,
    }
    axis.update(overrides)
    return axis


def _section_heading(title: str, sticker: str, accent: str) -> None:
    """Sticker-like section heading without changing the page structure."""

    st.markdown(
        f"""
        <div style="
            display:flex;
            align-items:center;
            gap:0.7rem;
            margin:0.25rem 0 0.85rem 0;
        ">
            <span style="
                display:inline-flex;
                align-items:center;
                justify-content:center;
                width:42px;
                height:42px;
                flex-shrink:0;
                background:{accent};
                color:#29282D;
                border:2px solid {OUTLINE};
                border-radius:13px;
                font-size:1.35rem;
                box-shadow:3px 3px 0 {OUTLINE};
                transform:rotate(-3deg);
            ">{sticker}</span>
            <span style="
                color:{LAV_100};
                font-family:'Bricolage Grotesque',sans-serif;
                font-size:1.35rem;
                font-weight:800;
                line-height:1.2;
            ">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _fmt_month(m: str) -> str:
    try:
        y, mo = m.split("-")
        return f"{month_abbr[int(mo)]} {y[2:]}"
    except (ValueError, IndexError, TypeError):
        return m


def _fmt(amount: float) -> str:
    return f"₹ {amount:,.2f}"


def _fmt_compact(amount: float) -> str:
    """Compact labels for chart centres and data points."""

    sign = "−" if amount < 0 else ""
    value = abs(amount)

    if value >= 10_000_000:
        return f"{sign}₹{value / 10_000_000:.2f}Cr"
    if value >= 100_000:
        return f"{sign}₹{value / 100_000:.2f}L"
    if value >= 1_000:
        return f"{sign}₹{value / 1_000:.1f}K"
    return f"{sign}₹{value:,.0f}"


def _visible_label_indices(values: list, limit: int = 8) -> set[int]:
    """
    Avoid unreadable label collisions on long time series.

    Short series display every value. Longer series display the latest,
    largest and smallest values so important points remain identifiable.
    """

    if len(values) <= limit:
        return set(range(len(values)))

    indices = {len(values) - 1}

    if values:
        indices.add(max(range(len(values)), key=lambda i: values[i]))
        indices.add(min(range(len(values)), key=lambda i: values[i]))

    return indices


def _chart_config() -> dict:
    return {
        "displayModeBar": False,
        "responsive": True,
        "scrollZoom": False,
    }


# ---------------------------------------------------------------------------
# Alert settings
# ---------------------------------------------------------------------------

def _alert_settings() -> tuple[float, float]:
    with st.expander("⚙️  Alert Settings", expanded=False):
        st.markdown(
            f"<p style='color:{TEXT_SECONDARY}; font-size:0.85rem;'>"
            "Alerts use two transparent rules:<br>"
            "<strong>Rule 1</strong> — A single expense above the absolute threshold.<br>"
            "<strong>Rule 2</strong> — A single expense ≥ N× the historical "
            "category average (needs at least 3 past transactions in that category)."
            "</p>",
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
# Section 1: Expense distribution
# ---------------------------------------------------------------------------

def _section_category_distribution(transactions: list):
    _section_heading(
        "Expense Distribution by Category",
        "✦",
        ACC_YELLOW,
    )

    cb = ae.category_breakdown(transactions, "expense")

    if not cb:
        st.info("No expense data yet.", icon="ℹ️")
        return

    labels = list(cb.keys())
    values = list(cb.values())

    colors = [
        _PLOTLY_COLORS[i % len(_PLOTLY_COLORS)]
        for i in range(len(labels))
    ]

    total_expense = sum(values)

    col_pie, col_bar = st.columns([2, 3], gap="medium")

    # ---- Donut chart -------------------------------------------------------
    with col_pie:
        fig = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.60,
                sort=False,
                direction="clockwise",
                marker=dict(
                    colors=colors,
                    line=dict(color=OUTLINE, width=3),
                ),
                textinfo="percent",
                textposition="inside",
                textfont=dict(
                    family="Bricolage Grotesque, Figtree, sans-serif",
                    color="#FFFFFF",
                    size=12,
                ),
                insidetextorientation="auto",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Spent: ₹%{value:,.2f}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            **_plotly_layout(
                "Where Your Money Goes",
                height=410,
                margin=dict(l=8, r=8, t=62, b=90),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    x=0.5,
                    xanchor="center",
                    y=-0.10,
                    yanchor="top",
                    font=dict(color=TEXT_PRIMARY, size=10),
                    entrywidth=100,
                    entrywidthmode="pixels",
                ),
                annotations=[
                    dict(
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        text=(
                            "<span style='font-size:11px;color:#BDB7C7'>"
                            "TOTAL SPENT</span><br>"
                            f"<b>{_fmt_compact(total_expense)}</b>"
                        ),
                        showarrow=False,
                        align="center",
                        font=dict(
                            family="Bricolage Grotesque, Figtree, sans-serif",
                            color=TEXT_PRIMARY,
                            size=17,
                        ),
                    )
                ],
            )
        )

        with st.container(border=True):
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

    # ---- Category bars: highest spending first ----------------------------
    with col_bar:
        ranked = sorted(
            zip(labels, values, colors),
            key=lambda item: item[1],
            reverse=True,
        )

        bar_labels = [item[0] for item in ranked]
        bar_values = [item[1] for item in ranked]
        bar_colors = [item[2] for item in ranked]

        max_value = max(bar_values) if bar_values else 0
        x_max = max_value * 1.28 if max_value > 0 else 1

        fig2 = go.Figure(
            go.Bar(
                x=bar_values,
                y=bar_labels,
                orientation="h",
                marker=dict(
                    color=bar_colors,
                    line=dict(color=OUTLINE, width=1.5),
                ),
                text=[_fmt_compact(v) for v in bar_values],
                textposition="outside",
                textfont=dict(
                    family="Bricolage Grotesque, Figtree, sans-serif",
                    color=TEXT_PRIMARY,
                    size=11,
                ),
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Spent: ₹%{x:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

        fig2.update_layout(
            **_plotly_layout(
                "Category Spending · Ranked",
                height=max(390, min(650, len(bar_labels) * 42 + 105)),
                margin=dict(l=15, r=65, t=62, b=40),
                showlegend=False,
                xaxis=_axis_style(
                    showgrid=True,
                    tickprefix="₹",
                    tickformat="~s",
                    range=[0, x_max],
                    title=None,
                ),
                yaxis=_axis_style(
                    showgrid=False,
                    autorange="reversed",
                    title=None,
                    tickfont=dict(
                        family="Figtree, sans-serif",
                        color=TEXT_PRIMARY,
                        size=11,
                    ),
                ),
            )
        )

        with st.container(border=True):
            st.plotly_chart(
                fig2,
                use_container_width=True,
                config=_chart_config(),
            )


# ---------------------------------------------------------------------------
# Section 2: Monthly expense trend
# ---------------------------------------------------------------------------

def _section_monthly_expense_trend(transactions: list):
    _section_heading(
        "Monthly Expense Trend",
        "↗",
        ACC_PINK,
    )

    mt = ae.monthly_trend(transactions, "expense")

    if not mt:
        st.info("No expense data to plot.", icon="ℹ️")
        return

    if len(mt) == 1:
        st.info(
            f"Only one month of data ({_fmt_month(mt[0]['month'])}). "
            "Add transactions from more months to see a trend.",
            icon="ℹ️",
        )

    xlabels = [_fmt_month(r["month"]) for r in mt]
    values = [r["amount"] for r in mt]
    visible_indices = _visible_label_indices(values)

    # Text is selectively displayed for long series to prevent collisions.
    point_labels = [
        _fmt_compact(value) if i in visible_indices else ""
        for i, value in enumerate(values)
    ]

    fig = go.Figure()

    # Soft pink area beneath the line.
    fig.add_trace(
        go.Scatter(
            x=xlabels,
            y=values,
            mode="lines",
            name="Expense area",
            line=dict(width=0, color=EXPENSE_COLOR),
            fill="tozeroy",
            fillcolor="rgba(240,138,154,0.13)",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Main expense line with bold markers and direct data labels.
    fig.add_trace(
        go.Scatter(
            x=xlabels,
            y=values,
            mode="lines+markers+text",
            name="Expenses",
            line=dict(
                color=EXPENSE_COLOR,
                width=4,
                shape="linear",
            ),
            marker=dict(
                size=11,
                color=EXPENSE_COLOR,
                line=dict(color=OUTLINE, width=2.5),
                symbol="circle",
            ),
            text=point_labels,
            textposition="top center",
            textfont=dict(
                family="Bricolage Grotesque, Figtree, sans-serif",
                color=TEXT_PRIMARY,
                size=11,
            ),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Expenses: ₹%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        **_plotly_layout(
            "Monthly Total Expenses",
            height=425,
            margin=dict(l=25, r=35, t=80, b=65),
            hovermode="x unified",
            showlegend=False,
            xaxis=_axis_style(
                showgrid=False,
                tickangle=-30 if len(xlabels) > 6 else 0,
                title=None,
                tickfont=dict(color=TEXT_SECONDARY, size=11),
            ),
            yaxis=_axis_style(
                tickprefix="₹",
                tickformat="~s",
                rangemode="tozero",
                title=None,
                zeroline=True,
                zerolinecolor=GRID_COLOR,
                zerolinewidth=1,
            ),
        )
    )

    with st.container(border=True):
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=_chart_config(),
        )


# ---------------------------------------------------------------------------
# Section 3: Income vs expenses
# ---------------------------------------------------------------------------

def _section_income_vs_expense(transactions: list):
    _section_heading(
        "Income vs Expense by Month",
        "↔",
        ACC_MINT,
    )

    ive = ae.income_vs_expense_monthly(transactions)

    if not ive:
        st.info("No data available.", icon="ℹ️")
        return

    xlabels = [_fmt_month(r["month"]) for r in ive]
    incomes = [r["income"] for r in ive]
    expenses = [r["expense"] for r in ive]
    nets = [r["net"] for r in ive]

    # Keep the graph legible when the dataset covers many months.
    income_visible = _visible_label_indices(incomes)
    expense_visible = _visible_label_indices(expenses)
    net_visible = _visible_label_indices(nets)

    income_labels = [
        _fmt_compact(v) if i in income_visible else ""
        for i, v in enumerate(incomes)
    ]
    expense_labels = [
        _fmt_compact(v) if i in expense_visible else ""
        for i, v in enumerate(expenses)
    ]
    net_labels = [
        _fmt_compact(v) if i in net_visible else ""
        for i, v in enumerate(nets)
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Income",
            x=xlabels,
            y=incomes,
            marker=dict(
                color=INCOME_COLOR,
                line=dict(color=OUTLINE, width=1.5),
            ),
            text=income_labels,
            textposition="outside",
            textfont=dict(
                family="Bricolage Grotesque, Figtree, sans-serif",
                color=TEXT_PRIMARY,
                size=10,
            ),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Income: ₹%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Bar(
            name="Expenses",
            x=xlabels,
            y=expenses,
            marker=dict(
                color=EXPENSE_COLOR,
                line=dict(color=OUTLINE, width=1.5),
            ),
            text=expense_labels,
            textposition="outside",
            textfont=dict(
                family="Bricolage Grotesque, Figtree, sans-serif",
                color=TEXT_PRIMARY,
                size=10,
            ),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Expenses: ₹%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    # Net can be negative; retain its original values and allow the axis
    # to accommodate both positive and negative balances.
    fig.add_trace(
        go.Scatter(
            name="Net balance",
            x=xlabels,
            y=nets,
            mode="lines+markers+text",
            line=dict(
                color=LAV_200,
                width=3.5,
                dash="dot",
            ),
            marker=dict(
                size=9,
                color=LAV_200,
                line=dict(color=OUTLINE, width=2),
                symbol="diamond",
            ),
            text=net_labels,
            textposition="top center",
            textfont=dict(
                family="Bricolage Grotesque, Figtree, sans-serif",
                color=LAV_100,
                size=10,
            ),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Net balance: ₹%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        **_plotly_layout(
            "Monthly Income, Expenses & Net Balance",
            barmode="group",
            bargap=0.28,
            bargroupgap=0.10,
            height=490,
            margin=dict(l=25, r=30, t=95, b=70),
            hovermode="x unified",
            xaxis=_axis_style(
                showgrid=False,
                tickangle=-30 if len(xlabels) > 6 else 0,
                title=None,
                tickfont=dict(color=TEXT_SECONDARY, size=11),
            ),
            yaxis=_axis_style(
                tickprefix="₹",
                tickformat="~s",
                title=None,
                zeroline=True,
                zerolinecolor=TEXT_SECONDARY,
                zerolinewidth=1.2,
                # Do not force zero as the lower bound: net balance may
                # be negative, and those values must remain visible.
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                title_text="",
                font=dict(color=TEXT_PRIMARY, size=11),
                itemwidth=90,
            ),
        )
    )

    with st.container(border=True):
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=_chart_config(),
        )


# ---------------------------------------------------------------------------
# Section 4: Unusual spending alerts
# ---------------------------------------------------------------------------

def _section_alerts(
    transactions: list,
    abs_thresh: float,
    rel_mult: float,
):
    _section_heading(
        "Unusual Spending Alerts",
        "!",
        ACC_YELLOW,
    )

    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; font-size:0.88rem; margin-top:0;'>"
        "Each alert is generated by a transparent rule — no machine learning. "
        "Adjust thresholds in <strong>Alert Settings</strong> above.</p>",
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
            f"(absolute > ₹{abs_thresh:,.0f}, "
            f"relative > {rel_mult:.1f}× average).",
            icon="✅",
        )
        return

    sev_colors = {
        "high": EXPENSE_COLOR,
        "medium": ACC_YELLOW,
    }

    rule_labels = {
        "absolute": "Rule 1 · Absolute threshold",
        "relative": "Rule 2 · Above category average",
    }

    for alert in alerts:
        sev = alert.get("severity", "medium")
        color = sev_colors.get(sev, LAV_400)
        rule = rule_labels.get(alert.get("rule", "absolute"), "")

        st.markdown(
            f"""
            <div style="
                background:{CARD_HIGH};
                border:2px solid {OUTLINE};
                border-left:6px solid {color};
                border-radius:16px;
                padding:1rem 1.1rem;
                margin-bottom:0.9rem;
                box-shadow:4px 4px 0 {OUTLINE};
            ">
                <div style="
                    display:flex;
                    flex-wrap:wrap;
                    gap:0.5rem 1rem;
                    justify-content:space-between;
                    align-items:center;
                ">
                    <span style="
                        color:{TEXT_PRIMARY};
                        font-family:'Bricolage Grotesque',sans-serif;
                        font-weight:800;
                    ">
                        #{alert['tx_id']} · {alert['category']} · {alert['date']}
                    </span>
                    <span style="
                        color:{color};
                        font-weight:800;
                        font-size:1.1rem;
                        white-space:nowrap;
                    ">
                        ₹{alert['amount']:,.2f}
                    </span>
                </div>
                <div style="
                    color:{TEXT_SECONDARY};
                    font-size:0.88rem;
                    margin-top:0.5rem;
                    line-height:1.55;
                ">
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
        f"""
        <div style="
        margin-top:1rem;
        margin-bottom:0.35rem;
        padding-top:0.5rem;
        overflow:visible;
        ">
            <div style="
                display:inline-block;
                color:{LAV_100};
                font-family:'Bricolage Grotesque',sans-serif;
                font-size:2rem;
                font-weight:800;
                line-height:1.4;
                letter-spacing:-0.02em;
                padding:0.1rem 0 0.2rem;
                overflow:visible;
            ">Analytics <span style="color:{ACC_YELLOW};">✳</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0.3rem; "
        "margin-bottom:1.2rem;'>"
        "Your money, decoded — colourful charts, clear numbers, "
        "and explainable spending alerts.</p>",
        unsafe_allow_html=True,
    )

    abs_thresh, rel_mult = _alert_settings()

    # Load transactions read-only. No JSON writes or data changes here.
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
