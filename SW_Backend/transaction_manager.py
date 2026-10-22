"""
transaction_manager.py
======================

Core CRUD logic and data validation for the SpendWise backend.

Responsibility:
    Create, read, update and delete transactions, validating every input
    against the SpendWise schema. All file access is delegated to
    data_manager.py. No budgets, balances or analytics live here.

Transaction schema (field names must not change):
    {
        "id": 1,
        "date": "2026-10-22",
        "amount": 450.0,
        "type": "expense",
        "category": "Food",
        "payment_method": "UPI",
        "note": "Dinner"
    }

Public API:
    add_transaction(...)         -> dict
    get_transactions(...)        -> list[dict]
    get_transaction_by_id(id)    -> dict
    update_transaction(id, **u)  -> dict
    delete_transaction(id)       -> bool

All invalid input raises ValueError.
"""

import math
from datetime import datetime

import data_manager

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------
VALID_TYPES = ("income", "expense")

EXPENSE_CATEGORIES = (
    "Food", "Transport", "Shopping", "Education",
    "Entertainment", "Bills", "Healthcare", "Other",
)
INCOME_CATEGORIES = ("Salary", "Allowance", "Freelance", "Other")

VALID_PAYMENT_METHODS = (
    "Cash", "UPI", "Debit Card", "Credit Card", "Bank Transfer", "Other",
)

DATE_FORMAT = "%Y-%m-%d"

# Fields a caller may change through update_transaction(). "id" is
# deliberately excluded: an id is permanent once assigned.
UPDATABLE_FIELDS = ("date", "amount", "type", "category", "payment_method", "note")


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------
def _validate_date(date) -> str:
    """Return `date` if it is a real calendar date in strict YYYY-MM-DD form."""
    if not isinstance(date, str):
        raise ValueError("date must be a string in YYYY-MM-DD format.")
    try:
        parsed = datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        raise ValueError(
            f"Invalid date '{date}'. Use a real date in YYYY-MM-DD format."
        )
    # strptime is lenient (it accepts '2026-1-5'); insist on zero-padding.
    if parsed.strftime(DATE_FORMAT) != date:
        raise ValueError(
            f"Invalid date '{date}'. Use zero-padded YYYY-MM-DD format."
        )
    return date


def _validate_amount(amount) -> float:
    """Return `amount` as a float if it is a finite number greater than 0."""
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number.")
    amount = float(amount)
    if math.isnan(amount) or math.isinf(amount):
        raise ValueError("amount must be a finite number.")
    if amount <= 0:
        raise ValueError("amount must be greater than 0.")
    return amount


def _validate_type(type_value) -> str:
    """Return the transaction type if it is 'income' or 'expense'."""
    if type_value not in VALID_TYPES:
        raise ValueError(
            f"Invalid type '{type_value}'. Allowed: {', '.join(VALID_TYPES)}."
        )
    return type_value


def _validate_category(category, type_value) -> str:
    """Return the category if it is allowed for the given (valid) type."""
    allowed = EXPENSE_CATEGORIES if type_value == "expense" else INCOME_CATEGORIES
    if category not in allowed:
        raise ValueError(
            f"Invalid category '{category}' for type '{type_value}'. "
            f"Allowed: {', '.join(allowed)}."
        )
    return category


def _validate_payment_method(payment_method) -> str:
    """Return the payment method if it is one of the allowed values."""
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ValueError(
            f"Invalid payment_method '{payment_method}'. "
            f"Allowed: {', '.join(VALID_PAYMENT_METHODS)}."
        )
    return payment_method


def _validate_note(note) -> str:
    """Return the note as a stripped string (None is treated as empty)."""
    if note is None:
        return ""
    if not isinstance(note, str):
        raise ValueError("note must be a string.")
    return note.strip()


def _validate_record(date, amount, type_value, category, payment_method, note) -> dict:
    """
    Validate all fields together and return them in a clean dictionary.

    The type is validated before the category because the set of allowed
    categories depends on it.
    """
    return {
        "date": _validate_date(date),
        "amount": _validate_amount(amount),
        "type": _validate_type(type_value),
        "category": _validate_category(category, _validate_type(type_value)),
        "payment_method": _validate_payment_method(payment_method),
        "note": _validate_note(note),
    }


def _generate_id(transactions: list) -> int:
    """
    Generate a unique integer id: one more than the largest existing id.

    Ids that are not integers (e.g. hand-edited data) are ignored when
    computing the maximum. The first transaction gets id 1.
    """
    existing = [
        t["id"] for t in transactions
        if isinstance(t, dict)
        and isinstance(t.get("id"), int)
        and not isinstance(t.get("id"), bool)
    ]
    return (max(existing) + 1) if existing else 1


def _find_index(transactions: list, transaction_id) -> int:
    """
    Return the list index of the transaction with the given id.

    Ids are compared as strings so that 3 and "3" both match; this is handy
    when an id comes back from a UI widget as text.

    Raises:
        ValueError: If the id is missing/invalid or no transaction has it.
    """
    if transaction_id is None or isinstance(transaction_id, bool):
        raise ValueError(f"Invalid transaction id: {transaction_id!r}.")
    target = str(transaction_id).strip()
    for index, transaction in enumerate(transactions):
        if isinstance(transaction, dict) and str(transaction.get("id")) == target:
            return index
    raise ValueError(f"Transaction with id {transaction_id!r} does not exist.")


def _validate_filter_amount(value, name: str):
    """Validate an optional min/max amount filter (None is allowed)."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")
    if math.isnan(value):
        raise ValueError(f"{name} must be a number.")
    return float(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def add_transaction(date: str, amount: float, type: str, category: str,
                    payment_method: str, note: str = "") -> dict:
    """
    Validate and store a new transaction.

    Args:
        date:           Date string in YYYY-MM-DD format.
        amount:         Positive number.
        type:           "income" or "expense".
        category:       Must belong to the category list for `type`.
        payment_method: One of the allowed payment methods.
        note:           Optional free-text note.

    Returns:
        The newly created transaction dictionary.

    Raises:
        ValueError: If any input is invalid.
    """
    # Validate first so nothing is read from or written to disk on bad input.
    clean = _validate_record(date, amount, type, category, payment_method, note)

    transactions = data_manager.load_data()

    # Build the dictionary with the exact schema field names and order.
    transaction = {
        "id": _generate_id(transactions),
        "date": clean["date"],
        "amount": clean["amount"],
        "type": clean["type"],
        "category": clean["category"],
        "payment_method": clean["payment_method"],
        "note": clean["note"],
    }

    transactions.append(transaction)
    data_manager.save_data(transactions)
    return transaction


def get_transactions(start_date: str = None, end_date: str = None,
                     type: str = None, category: str = None,
                     payment_method: str = None, min_amount: float = None,
                     max_amount: float = None) -> list[dict]:
    """
    Retrieve transactions, optionally filtered. Filters combine with AND.

    Args:
        start_date:     Include transactions on or after this date (inclusive).
        end_date:       Include transactions on or before this date (inclusive).
        type:           Keep only this type ("income" / "expense").
        category:       Keep only this category.
        payment_method: Keep only this payment method.
        min_amount:     Keep only amounts >= this value.
        max_amount:     Keep only amounts <= this value.

    Returns:
        A list of matching transaction dictionaries; [] if none match.

    Raises:
        ValueError: If a date or amount filter is malformed.
    """
    # Validate the filter arguments that have a format.
    if start_date is not None:
        _validate_date(start_date)
    if end_date is not None:
        _validate_date(end_date)
    min_amount = _validate_filter_amount(min_amount, "min_amount")
    max_amount = _validate_filter_amount(max_amount, "max_amount")

    results = []
    for t in data_manager.load_data():
        if not isinstance(t, dict):
            continue  # skip malformed entries rather than crash

        # YYYY-MM-DD strings sort chronologically, so plain string
        # comparison is a correct date comparison.
        if start_date is not None and t.get("date", "") < start_date:
            continue
        if end_date is not None and t.get("date", "") > end_date:
            continue
        if type is not None and t.get("type") != type:
            continue
        if category is not None and t.get("category") != category:
            continue
        if payment_method is not None and t.get("payment_method") != payment_method:
            continue
        if min_amount is not None and t.get("amount", 0) < min_amount:
            continue
        if max_amount is not None and t.get("amount", 0) > max_amount:
            continue

        results.append(t)

    return results


def get_transaction_by_id(transaction_id) -> dict:
    """
    Find a single transaction by id.

    Returns:
        The matching transaction dictionary.

    Raises:
        ValueError: If no transaction has that id.
    """
    transactions = data_manager.load_data()
    return transactions[_find_index(transactions, transaction_id)]


def update_transaction(transaction_id, **updates) -> dict:
    """
    Update only the supplied fields of an existing transaction.

    Allowed keyword arguments: date, amount, type, category,
    payment_method, note. The id cannot be changed.

    The merged result is validated as a whole, so for example changing
    `type` from "expense" to "income" without also supplying a compatible
    `category` is rejected.

    Returns:
        The updated transaction dictionary.

    Raises:
        ValueError: If the id is not found, an unknown field is supplied,
                    no updates are given, or validation fails.
    """
    unknown = [key for key in updates if key not in UPDATABLE_FIELDS]
    if unknown:
        raise ValueError(
            f"Cannot update field(s): {', '.join(unknown)}. "
            f"Allowed: {', '.join(UPDATABLE_FIELDS)}."
        )
    if not updates:
        raise ValueError("No fields were provided to update.")

    transactions = data_manager.load_data()
    index = _find_index(transactions, transaction_id)

    # Merge the changes onto a copy of the stored record and validate the
    # whole result. Nothing is saved unless every check passes.
    merged = {**transactions[index], **updates}
    clean = _validate_record(
        merged.get("date"),
        merged.get("amount"),
        merged.get("type"),
        merged.get("category"),
        merged.get("payment_method"),
        merged.get("note", ""),
    )

    updated = {"id": transactions[index]["id"], **clean}
    transactions[index] = updated
    data_manager.save_data(transactions)
    return updated


def delete_transaction(transaction_id) -> bool:
    """
    Remove a transaction by id.

    Returns:
        True if the transaction was deleted.

    Raises:
        ValueError: If no transaction has that id.
    """
    transactions = data_manager.load_data()
    index = _find_index(transactions, transaction_id)
    transactions.pop(index)
    data_manager.save_data(transactions)
    return True


# ---------------------------------------------------------------------------
# Demo: run with `python transaction_manager.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== SpendWise backend demo ===\n")

    # 1. ADD
    created = add_transaction(
        date="2026-10-22",
        amount=450.0,
        type="expense",
        category="Food",
        payment_method="UPI",
        note="Dinner",
    )
    print("1. Added:", created)

    # 2. RETRIEVE (with filters)
    food_expenses = get_transactions(
        start_date="2026-10-01",
        end_date="2026-10-31",
        type="expense",
        category="Food",
    )
    print(f"\n2. Food expenses in October 2026 ({len(food_expenses)} found):")
    for item in food_expenses:
        print("  ", item)

    print("\n   Lookup by id:", get_transaction_by_id(created["id"]))

    # 3. UPDATE
    updated = update_transaction(created["id"], amount=500.0, note="Dinner with friends")
    print("\n3. Updated:", updated)

    # Show that validation works: this raises ValueError and changes nothing.
    try:
        update_transaction(created["id"], amount=-10)
    except ValueError as error:
        print("   Rejected invalid update ->", error)

    # 4. DELETE
    print("\n4. Deleted:", delete_transaction(created["id"]))

    # Confirm the id is really gone.
    try:
        get_transaction_by_id(created["id"])
    except ValueError as error:
        print("   Confirmed gone ->", error)
