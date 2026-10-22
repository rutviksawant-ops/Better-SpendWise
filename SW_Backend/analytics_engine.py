"""
analytics_engine.py
===================
Pure calculation functions for SpendWise analytics.

Responsibility:
    Derive insights from a list of transaction dicts.  No file I/O, no
    Streamlit, no machine learning.  Every alert is based on a transparent,
    explainable rule that can be restated to a student in one sentence.

Public API:
    summary(transactions, start_date, end_date)    -> dict
    category_breakdown(transactions, tx_type)      -> dict[str, float]
    monthly_trend(transactions, tx_type)           -> list[dict]
    income_vs_expense_monthly(transactions)        -> list[dict]
    savings_rate(income, expense)                  -> float | None
    unusual_spending_alerts(transactions,
                            abs_threshold,
                            relative_multiplier)   -> list[dict]

All functions are stateless and side-effect-free.
All date parameters are strings in YYYY-MM-DD format.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, date

DATE_FMT = "%Y-%m-%d"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _parse_date(d: str) -> date:
    return datetime.strptime(d, DATE_FMT).date()


def _in_range(tx_date: str, start: str | None, end: str | None) -> bool:
    """YYYY-MM-DD strings compare lexicographically — valid date ordering."""
    if start and tx_date < start:
        return False
    if end and tx_date > end:
        return False
    return True


def _filter(transactions: list, start_date: str | None = None,
            end_date: str | None = None, tx_type: str | None = None) -> list:
    result = []
    for t in transactions:
        if not isinstance(t, dict):
            continue
        td = t.get("date", "")
        if not _in_range(td, start_date, end_date):
            continue
        if tx_type and t.get("type") != tx_type:
            continue
        result.append(t)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def summary(transactions: list,
            start_date: str | None = None,
            end_date: str | None = None) -> dict:
    """
    Compute headline figures for a set of transactions (optionally filtered
    to a date range).

    Returns:
        {
            "total_income":   float,
            "total_expense":  float,
            "net":            float,   # income - expense
            "savings_rate":   float | None,   # None when income == 0
            "tx_count":       int,
            "income_count":   int,
            "expense_count":  int,
        }
    """
    visible = _filter(transactions, start_date, end_date)
    income  = sum(t["amount"] for t in visible if t.get("type") == "income")
    expense = sum(t["amount"] for t in visible if t.get("type") == "expense")
    return {
        "total_income":  round(income, 2),
        "total_expense": round(expense, 2),
        "net":           round(income - expense, 2),
        "savings_rate":  savings_rate(income, expense),
        "tx_count":      len(visible),
        "income_count":  sum(1 for t in visible if t.get("type") == "income"),
        "expense_count": sum(1 for t in visible if t.get("type") == "expense"),
    }


def savings_rate(income: float, expense: float) -> float | None:
    """
    Return savings as a percentage of income.

    Returns None when income is 0 (division undefined).
    Returns a negative value when expenses exceed income.
    """
    if income == 0:
        return None
    return round((income - expense) / income * 100, 1)


def category_breakdown(transactions: list,
                       tx_type: str = "expense",
                       start_date: str | None = None,
                       end_date: str | None = None) -> dict[str, float]:
    """
    Total amount per category for the given type and optional date range.

    Returns:
        {"Food": 1540.0, "Transport": 230.0, ...}   sorted by amount desc.
    """
    visible = _filter(transactions, start_date, end_date, tx_type)
    totals: dict[str, float] = defaultdict(float)
    for t in visible:
        totals[t.get("category", "Other")] += t.get("amount", 0)
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def monthly_trend(transactions: list,
                  tx_type: str = "expense") -> list[dict]:
    """
    Total amount per calendar month for the given transaction type.

    Returns:
        [
            {"month": "2026-09", "amount": 3200.0},
            {"month": "2026-10", "amount": 4100.0},
            ...
        ]
        Sorted chronologically.
    """
    by_month: dict[str, float] = defaultdict(float)
    for t in transactions:
        if not isinstance(t, dict):
            continue
        if t.get("type") != tx_type:
            continue
        d = t.get("date", "")
        if len(d) >= 7:
            by_month[d[:7]] += t.get("amount", 0)
    return [
        {"month": m, "amount": round(v, 2)}
        for m, v in sorted(by_month.items())
    ]


def income_vs_expense_monthly(transactions: list) -> list[dict]:
    """
    Side-by-side income and expense totals per calendar month.

    Returns:
        [
            {"month": "2026-09", "income": 8000.0, "expense": 3200.0, "net": 4800.0},
            ...
        ]
        Sorted chronologically.
    """
    income_by_month:  dict[str, float] = defaultdict(float)
    expense_by_month: dict[str, float] = defaultdict(float)

    for t in transactions:
        if not isinstance(t, dict):
            continue
        d = t.get("date", "")
        if len(d) < 7:
            continue
        m = d[:7]
        if t.get("type") == "income":
            income_by_month[m] += t.get("amount", 0)
        elif t.get("type") == "expense":
            expense_by_month[m] += t.get("amount", 0)

    all_months = sorted(set(income_by_month) | set(expense_by_month))
    result = []
    for m in all_months:
        inc = income_by_month.get(m, 0.0)
        exp = expense_by_month.get(m, 0.0)
        result.append({
            "month":   m,
            "income":  round(inc, 2),
            "expense": round(exp, 2),
            "net":     round(inc - exp, 2),
        })
    return result


def recent_transactions(transactions: list, n: int = 5) -> list[dict]:
    """Return the n most recent transactions, newest first."""
    valid = [t for t in transactions if isinstance(t, dict) and t.get("date")]
    return sorted(valid, key=lambda t: t["date"], reverse=True)[:n]


def unusual_spending_alerts(
    transactions: list,
    abs_threshold: float = 5000.0,
    relative_multiplier: float = 2.5,
    min_history_count: int = 3,
) -> list[dict]:
    """
    Identify potentially unusual expense transactions using two transparent rules.

    Rule 1 — Absolute threshold:
        Any single expense transaction with amount > abs_threshold is flagged.
        Reason shown to user: "This single transaction of ₹X exceeds the
        configured alert threshold of ₹Y."

    Rule 2 — Historical category average:
        For categories that have at least min_history_count prior transactions,
        any new transaction whose amount is >= relative_multiplier times the
        category average is flagged.
        Reason shown to user: "This ₹X [Category] expense is Nx the average
        (₹Y) based on the last Z transactions in this category."

    Neither rule involves machine learning or external data.

    Args:
        transactions:        Full list of transaction dicts (newest last or
                             any order; the function sorts internally).
        abs_threshold:       Rupee amount above which a single expense is flagged.
        relative_multiplier: Factor above category average that triggers a flag.
        min_history_count:   Minimum prior transactions needed to apply Rule 2.

    Returns:
        List of alert dicts, sorted by date descending::

            [
                {
                    "tx_id":       3,
                    "date":        "2026-10-22",
                    "category":    "Food",
                    "amount":      12000.0,
                    "rule":        "absolute" | "relative",
                    "reason":      "Human-readable explanation.",
                    "severity":    "high" | "medium",
                },
                ...
            ]
    """
    expenses = sorted(
        [t for t in transactions if isinstance(t, dict) and t.get("type") == "expense"],
        key=lambda t: t.get("date", ""),
    )

    # Build per-category history list (all expenses, ordered by date)
    cat_history: dict[str, list[float]] = defaultdict(list)
    for t in expenses:
        cat_history[t.get("category", "Other")].append(t.get("amount", 0.0))

    alerts: list[dict] = []
    seen_ids: set = set()   # avoid duplicate alerts for the same transaction

    for t in expenses:
        tx_id  = t.get("id")
        amount = t.get("amount", 0.0)
        cat    = t.get("category", "Other")
        d      = t.get("date", "")

        # Rule 1: absolute threshold
        if amount > abs_threshold:
            if tx_id not in seen_ids:
                alerts.append({
                    "tx_id":    tx_id,
                    "date":     d,
                    "category": cat,
                    "amount":   amount,
                    "rule":     "absolute",
                    "reason":   (
                        f"This single {cat} expense of ₹{amount:,.2f} exceeds "
                        f"the alert threshold of ₹{abs_threshold:,.2f}."
                    ),
                    "severity": "high",
                })
                seen_ids.add(tx_id)

        # Rule 2: relative to category average
        history = cat_history.get(cat, [])
        if len(history) >= min_history_count and tx_id not in seen_ids:
            # Use all values EXCEPT this transaction's own to form the baseline
            others = [v for v in history if v != amount] or history
            if others:
                avg = sum(others) / len(others)
                if avg > 0 and amount >= relative_multiplier * avg:
                    alerts.append({
                        "tx_id":    tx_id,
                        "date":     d,
                        "category": cat,
                        "amount":   amount,
                        "rule":     "relative",
                        "reason":   (
                            f"This {cat} expense of ₹{amount:,.2f} is "
                            f"{amount / avg:.1f}× the category average "
                            f"(₹{avg:,.2f} across {len(others)} transaction(s))."
                        ),
                        "severity": "medium",
                    })
                    seen_ids.add(tx_id)

    # Sort newest first
    return sorted(alerts, key=lambda a: a.get("date", ""), reverse=True)
