"""
pages/budgets.py
================
Budgets page for SpendWise.

Uses budget_manager for persistence and calculation.
Displays:
  - Overall monthly spending budget with progress bar and warning levels
  - Per-category budgets with the same treatment
  - Daily allowance
  - Unbudgeted category spending
  - Budget settings form (set/update/remove)
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
import budget_manager as bm

import streamlit as st
from datetime import date

from theme import (
    LAV_100, LAV_200, LAV_300, LAV_400, LAV_500,
    TEXT_PRIMARY, TEXT_SECONDARY,
    CARD_LOW, CARD_HIGH, BORDER, BG_DEEP,
    INCOME_COLOR, EXPENSE_COLOR,
)

# All expense categories from the backend
EXPENSE_CATS = list(tm.EXPENSE_CATEGORIES)

# Warning-level colour mapping
_LEVEL_COLOR = {
    "ok":        "#6EE7B7",   # green
    "warning":   "#FCD34D",   # amber  (≥70%)
    "danger":    "#F97316",   # orange (≥90%)
    "exceeded":  "#F87171",   # red    (≥100%)
    "no_budget": TEXT_SECONDARY,
}
_LEVEL_LABEL = {
    "ok":        "✅ On track",
    "warning":   "⚠️ 70%+ used",
    "danger":    "🔴 90%+ used",
    "exceeded":  "🚨 Budget exceeded",
    "no_budget": "— No budget set",
}


def _fmt(amount: float) -> str:
    return f"₹ {amount:,.2f}"


def _progress_bar_html(pct: float, level: str) -> str:
    """Render a styled HTML progress bar capped at 100% visually."""
    fill = min(pct, 100)
    color = _LEVEL_COLOR.get(level, LAV_400)
    return (
        f"<div style='background:{BORDER}; border-radius:6px; height:10px; overflow:hidden; margin:0.3rem 0;'>"
        f"<div style='width:{fill:.1f}%; background:{color}; height:100%; border-radius:6px; "
        f"transition:width 0.4s ease;'></div></div>"
    )


# ---------------------------------------------------------------------------
# Budget status card
# ---------------------------------------------------------------------------
def _status_card(name: str, block: dict, icon: str = "💰"):
    level  = block["level"]
    color  = _LEVEL_COLOR.get(level, LAV_400)
    label  = _LEVEL_LABEL.get(level, "")
    budget = block["budget"]
    spent  = block["spent"]
    pct    = block["pct_used"]

    badge_style = (
        f"background:{color}22; color:{color}; border:1px solid {color}44; "
        f"border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600;"
    )

    exceeded_row = ""
    if level == "exceeded":
        exceeded_row = (
            f"<div style='color:{EXPENSE_COLOR}; font-size:0.85rem; margin-top:0.2rem;'>"
            f"Exceeded by {_fmt(block['exceeded_by'])}</div>"
        )

    
    daily_row = ""
    if block["daily_allowance"] > 0:
        daily_row = (
            f"Daily allowance: {_fmt(block['daily_allowance'])}"
        )



    st.markdown(
        f"""
        <div style="background:{CARD_LOW}; border:1px solid {BORDER}; border-radius:12px;
                    padding:1rem 1.2rem; margin-bottom:0.8rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:{LAV_100}; font-weight:700; font-size:1rem;">{icon} {name}</span>
                <span style="{badge_style}">{label}</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.4rem; margin-top:0.6rem;">
                <div>
                    <div style="color:{TEXT_SECONDARY}; font-size:0.75rem;">Budget</div>
                    <div style="color:{TEXT_PRIMARY}; font-weight:600;">{_fmt(budget)}</div>
                </div>
                <div>
                    <div style="color:{TEXT_SECONDARY}; font-size:0.75rem;">Spent</div>
                    <div style="color:{color}; font-weight:600;">{_fmt(spent)}</div>
                </div>
                <div>
                    <div style="color:{TEXT_SECONDARY}; font-size:0.75rem;">Remaining</div>
                    <div style="color:{TEXT_PRIMARY}; font-weight:600;">{_fmt(block['remaining'])}</div>
                </div>
            </div>
            {_progress_bar_html(pct, level)}
            <div style="color:{TEXT_SECONDARY}; font-size:0.75rem; text-align:right;">
                {pct:.1f}% used
            </div>
            {exceeded_row}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if block["daily_allowance"] > 0:
        st.caption(
            f"Daily allowance: {_fmt(block['daily_allowance'])}"
        )



# ---------------------------------------------------------------------------
# Settings form
# ---------------------------------------------------------------------------
def _settings_form(budgets: dict):
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.3rem;'>⚙️ Budget Settings</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0;'>"
        f"Set monthly budgets. Use 0 to remove a category budget.</p>",
        unsafe_allow_html=True,
    )

    with st.form("form_budget_settings"):
        st.markdown(
            f"<p style='color:{LAV_300}; font-weight:600;'>Overall Monthly Budget</p>",
            unsafe_allow_html=True,
        )
        overall_val = st.number_input(
            "Overall monthly spending limit (₹)",
            min_value=0.0,
            value=float(budgets.get("overall", 0.0)),
            step=100.0,
            format="%.2f",
            help="Sets the total spending cap for any month. Use 0 to disable.",
            key="budget_overall_input",
        )

        st.markdown(
            f"<p style='color:{LAV_300}; font-weight:600; margin-top:1rem;'>Category Budgets</p>",
            unsafe_allow_html=True,
        )

        cat_cols = st.columns(2)
        cat_inputs: dict[str, float] = {}
        for i, cat in enumerate(EXPENSE_CATS):
            with cat_cols[i % 2]:
                existing = budgets.get("categories", {}).get(cat, 0.0)
                cat_inputs[cat] = st.number_input(
                    f"{cat} (₹/month)",
                    min_value=0.0,
                    value=float(existing),
                    step=100.0,
                    format="%.2f",
                    help=f"Monthly budget for {cat}. Use 0 to remove.",
                    key=f"budget_cat_{cat}",
                )

        saved = st.form_submit_button("💾  Save All Budgets", use_container_width=True)

    if saved:
        errors: list[str] = []
        try:
            bm.set_overall_budget(overall_val)
        except ValueError as e:
            errors.append(f"Overall budget: {e}")

        for cat, val in cat_inputs.items():
            try:
                bm.set_category_budget(cat, val)
            except ValueError as e:
                errors.append(f"{cat}: {e}")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}", icon="🚫")
        else:
            st.success("✅ Budgets saved successfully.", icon="✅")
            st.rerun()


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render():
    st.markdown(
        f"<h1 style='color:{LAV_100}; margin-bottom:0.1rem;'>🎯 Budgets</h1>",
        unsafe_allow_html=True,
    )

    today = date.today()
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0; margin-bottom:1.2rem;'>"
        f"Monthly budgets for <strong style='color:{LAV_300};'>"
        f"{today.strftime('%B %Y')}</strong>.</p>",
        unsafe_allow_html=True,
    )

    # ── Load data ─────────────────────────────────────────────────────────
    try:
        all_transactions = tm.get_transactions()
    except Exception as exc:
        st.error(f"Could not load transactions: {exc}", icon="❌")
        return

    budgets = bm.load_budgets()

    try:
        status = bm.get_budget_status(all_transactions, today.year, today.month)
    except Exception as exc:
        st.error(f"Could not calculate budget status: {exc}", icon="❌")
        return

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_status, tab_settings = st.tabs(["📊  Budget Status", "⚙️  Settings"])

    with tab_status:
        # Overall
        st.markdown(
            f"<h3 style='color:{LAV_200}; margin-bottom:0.6rem;'>Overall Spending</h3>",
            unsafe_allow_html=True,
        )

        overall = status["overall"]
        if overall["budget"] == 0:
            st.info(
                "No overall monthly budget set. "
                "Go to **Settings** to add one.",
                icon="ℹ️",
            )
        else:
            _status_card("Overall Monthly Budget", overall, "💰")

        # Per-category budgets
        cat_statuses = status.get("categories", {})
        if cat_statuses:
            st.markdown(
                f"<h3 style='color:{LAV_200}; margin:1rem 0 0.6rem;'>Category Budgets</h3>",
                unsafe_allow_html=True,
            )
            cc1, cc2 = st.columns(2)
            items = list(cat_statuses.items())
            for i, (cat, block) in enumerate(items):
                with (cc1 if i % 2 == 0 else cc2):
                    _status_card(cat, block, "📂")
        else:
            if cat_statuses is not None:
                st.info(
                    "No category budgets set. Go to **Settings** to add some.",
                    icon="ℹ️",
                )

        # Unbudgeted spending
        unbudgeted = status.get("unbudgeted_spend", {})
        if unbudgeted:
            st.markdown(
                f"<h3 style='color:{LAV_200}; margin:1rem 0 0.4rem;'>📋 Spending Without a Budget</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='color:{TEXT_SECONDARY}; font-size:0.85rem; margin-top:0;'>"
                f"These categories have spending this month but no budget assigned.</p>",
                unsafe_allow_html=True,
            )
            ub_cols = st.columns(min(len(unbudgeted), 4))
            for idx, (cat, amt) in enumerate(sorted(unbudgeted.items(), key=lambda x: -x[1])):
                with ub_cols[idx % len(ub_cols)]:
                    st.metric(cat, f"₹ {amt:,.2f}")

    with tab_settings:
        _settings_form(budgets)
