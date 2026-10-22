"""
budget_manager.py
=================
Budget persistence and calculation layer for SpendWise.

Responsibility:
    Store and retrieve monthly budget settings (one overall budget and
    zero or more category-specific budgets).  Calculate how much has been
    spent against each budget and derive useful display metrics.

Storage:
    <this file's folder>/data/budgets.json

Schema:
    {
        "overall": 10000.0,          # monthly overall spending limit (0 = not set)
        "categories": {
            "Food": 2000.0,
            "Transport": 500.0,
            ...
        }
    }

Public API (pure / calculation):
    load_budgets()                  -> dict
    save_budgets(budgets)           -> None
    set_overall_budget(amount)      -> dict
    set_category_budget(cat, amt)   -> dict
    remove_category_budget(cat)     -> dict
    get_budget_status(transactions, year, month) -> dict
    daily_allowance(remaining, year, month)      -> float

All invalid inputs raise ValueError.
Budgets are not transactions — never stored in transactions.json.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from calendar import monthrange
from datetime import date

# ---------------------------------------------------------------------------
# File location — anchored to this file, not cwd
# ---------------------------------------------------------------------------
_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR  = os.path.join(_BASE_DIR, "data")
_BUDGETS_FILE = os.path.join(_DATA_DIR, "budgets.json")

_EMPTY_BUDGETS: dict = {"overall": 0.0, "categories": {}}


# ---------------------------------------------------------------------------
# Internal I/O helpers
# ---------------------------------------------------------------------------
def _ensure_data_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def load_budgets() -> dict:
    """
    Read the budgets JSON file.

    Self-healing: returns the empty structure if the file is missing,
    empty, or corrupted.  Never raises on I/O problems.
    """
    _ensure_data_dir()
    if not os.path.exists(_BUDGETS_FILE):
        return {"overall": 0.0, "categories": {}}
    try:
        with open(_BUDGETS_FILE, "r", encoding="utf-8") as fh:
            content = fh.read()
        if not content.strip():
            return {"overall": 0.0, "categories": {}}
        data = json.loads(content)
        if not isinstance(data, dict):
            return {"overall": 0.0, "categories": {}}
        # Ensure both required keys exist and have the right types
        overall = data.get("overall", 0.0)
        if not isinstance(overall, (int, float)) or isinstance(overall, bool):
            overall = 0.0
        categories = data.get("categories", {})
        if not isinstance(categories, dict):
            categories = {}
        return {"overall": float(overall), "categories": dict(categories)}
    except (json.JSONDecodeError, OSError):
        return {"overall": 0.0, "categories": {}}


def save_budgets(budgets: dict) -> None:
    """
    Write the budget dict atomically.

    Args:
        budgets: dict with keys "overall" (float) and "categories" (dict).

    Raises:
        TypeError:  if budgets is not a dict.
        OSError:    if the file cannot be written.
    """
    if not isinstance(budgets, dict):
        raise TypeError("budgets must be a dict.")
    _ensure_data_dir()
    fd, tmp = tempfile.mkstemp(dir=_DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(budgets, fh, indent=4, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, _BUDGETS_FILE)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---------------------------------------------------------------------------
# Budget setters
# ---------------------------------------------------------------------------
def _validate_budget_amount(amount, name: str = "amount") -> float:
    """Return amount as a non-negative finite float."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError(f"{name} must be a number.")
    amount = float(amount)
    if math.isnan(amount) or math.isinf(amount):
        raise ValueError(f"{name} must be a finite number.")
    if amount < 0:
        raise ValueError(f"{name} must be 0 or greater (use 0 to clear a budget).")
    return amount


def set_overall_budget(amount) -> dict:
    """
    Set the monthly overall spending budget.

    Args:
        amount: Non-negative number.  0 clears the budget.

    Returns:
        Updated budgets dict.
    """
    clean = _validate_budget_amount(amount, "overall budget")
    budgets = load_budgets()
    budgets["overall"] = clean
    save_budgets(budgets)
    return budgets


def set_category_budget(category: str, amount) -> dict:
    """
    Set a monthly budget for one expense category.

    Args:
        category: Category name string (caller is responsible for using a
                  recognised category; budget_manager is category-agnostic).
        amount:   Non-negative number.  0 removes the category budget.

    Returns:
        Updated budgets dict.
    """
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category must be a non-empty string.")
    category = category.strip()
    clean = _validate_budget_amount(amount, f"budget for '{category}'")
    budgets = load_budgets()
    if clean == 0.0:
        budgets["categories"].pop(category, None)
    else:
        budgets["categories"][category] = clean
    save_budgets(budgets)
    return budgets


def remove_category_budget(category: str) -> dict:
    """Remove a specific category budget entirely."""
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category must be a non-empty string.")
    budgets = load_budgets()
    budgets["categories"].pop(category.strip(), None)
    save_budgets(budgets)
    return budgets


# ---------------------------------------------------------------------------
# Budget status calculation
# ---------------------------------------------------------------------------
def get_budget_status(transactions: list, year: int, month: int) -> dict:
    """
    Calculate budget usage for a given calendar month.

    Args:
        transactions: Full list of transaction dicts (from transaction_manager).
        year:         4-digit year.
        month:        Month number 1-12.

    Returns a dict with the following structure::

        {
            "year":  2026,
            "month": 10,
            "overall": {
                "budget":     10000.0,   # 0 if not set
                "spent":      4320.0,
                "remaining":  5680.0,    # capped at 0 when exceeded
                "exceeded_by": 0.0,      # amount over budget (0 if within)
                "pct_used":   43.2,      # 0-100+ (can exceed 100)
                "level":      "ok",      # "ok" | "warning" | "danger" | "exceeded"
                "daily_allowance": 213.1,# remaining / remaining days (0 if exceeded)
            },
            "categories": {
                "Food": {
                    "budget":      2000.0,
                    "spent":       1540.0,
                    "remaining":   460.0,
                    "exceeded_by": 0.0,
                    "pct_used":    77.0,
                    "level":       "warning",
                    "daily_allowance": 17.3,
                },
                ...
            },
            "unbudgeted_spend": {   # spending in categories with no budget set
                "Food": 0.0,        # omitted if a budget exists for the category
                ...
            },
        }
    """
    if not isinstance(year, int) or not isinstance(month, int):
        raise ValueError("year and month must be integers.")
    if not (1 <= month <= 12):
        raise ValueError("month must be between 1 and 12.")

    budgets = load_budgets()
    month_str = f"{year:04d}-{month:02d}"

    # Sum expenses for this month from the transaction list
    month_expenses: dict[str, float] = {}
    for t in transactions:
        if not isinstance(t, dict):
            continue
        if t.get("type") != "expense":
            continue
        tx_date = t.get("date", "")
        if not tx_date.startswith(month_str):
            continue
        cat = t.get("category", "Other")
        month_expenses[cat] = month_expenses.get(cat, 0.0) + float(t.get("amount", 0))

    total_spent = sum(month_expenses.values())

    # Days remaining in the month (inclusive of today)
    today = date.today()
    _, days_in_month = monthrange(year, month)
    if today.year == year and today.month == month:
        days_remaining = days_in_month - today.day + 1
    elif date(year, month, 1) > today:
        days_remaining = days_in_month   # whole month is in the future
    else:
        days_remaining = 0               # month is fully in the past

    def _level(pct: float) -> str:
        if pct >= 100:
            return "exceeded"
        if pct >= 90:
            return "danger"
        if pct >= 70:
            return "warning"
        return "ok"

    def _status_block(budget: float, spent: float) -> dict:
        remaining    = max(0.0, budget - spent) if budget > 0 else 0.0
        exceeded_by  = max(0.0, spent - budget) if budget > 0 else 0.0
        pct_used     = (spent / budget * 100) if budget > 0 else 0.0
        da           = daily_allowance(remaining, days_remaining)
        return {
            "budget":          round(budget, 2),
            "spent":           round(spent, 2),
            "remaining":       round(remaining, 2),
            "exceeded_by":     round(exceeded_by, 2),
            "pct_used":        round(pct_used, 1),
            "level":           _level(pct_used) if budget > 0 else "no_budget",
            "daily_allowance": round(da, 2),
        }

    # Overall
    overall_block = _status_block(budgets["overall"], total_spent)

    # Per-category
    cat_budgets = budgets.get("categories", {})
    cat_statuses: dict = {}
    unbudgeted: dict = {}
    all_cats = set(month_expenses.keys()) | set(cat_budgets.keys())
    for cat in sorted(all_cats):
        budget_amt = cat_budgets.get(cat, 0.0)
        spent_amt  = month_expenses.get(cat, 0.0)
        if budget_amt > 0:
            cat_statuses[cat] = _status_block(budget_amt, spent_amt)
        elif spent_amt > 0:
            unbudgeted[cat] = round(spent_amt, 2)

    return {
        "year":             year,
        "month":            month,
        "overall":          overall_block,
        "categories":       cat_statuses,
        "unbudgeted_spend": unbudgeted,
    }


def daily_allowance(remaining: float, days_remaining: int) -> float:
    """
    Calculate how much can be spent per day with the remaining budget.

    Args:
        remaining:      Remaining budget amount (>= 0).
        days_remaining: Number of days left in the period (>= 0).

    Returns:
        Daily allowance as a float.  Returns 0.0 when budget is exhausted
        or no days remain.
    """
    if remaining <= 0 or days_remaining <= 0:
        return 0.0
    return remaining / days_remaining
