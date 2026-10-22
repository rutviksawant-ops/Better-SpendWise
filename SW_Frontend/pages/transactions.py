
"""
pages/transactions.py
=====================
Full Transactions page for SpendWise.

Sections:
  1. Add Transaction
  2. All Transactions
  3. Edit Transaction
"""

from __future__ import annotations

import sys
import os
from datetime import date, datetime

# Ensure backend is reachable even if this module is imported before app.py
_BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "SW_Backend")
)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import transaction_manager as tm
import pandas as pd
import streamlit as st

from theme import (
    inject_css,
    INCOME_COLOR, EXPENSE_COLOR,
    LAV_100, LAV_200, LAV_300, LAV_400,
    TEXT_PRIMARY, TEXT_SECONDARY,
    CARD_LOW, CARD_HIGH, BORDER, BG_DEEP, BG_SURFACE,
)

# Constants mirrored from backend
VALID_TYPES = list(tm.VALID_TYPES)
EXPENSE_CATS = list(tm.EXPENSE_CATEGORIES)
INCOME_CATS = list(tm.INCOME_CATEGORIES)
PAYMENT_METHODS = list(tm.VALID_PAYMENT_METHODS)
DATE_FMT = "%Y-%m-%d"


# ── Helpers ────────────────────────────────────────────────────────────────

def _fmt_amount(amount: float) -> str:
    return f"₹ {amount:,.2f}"


def _type_badge(t_type: str) -> str:
    if t_type == "income":
        return '<span class="sw-badge-income">▲ Income</span>'
    return '<span class="sw-badge-expense">▼ Expense</span>'


def _clear_add_form():
    """Reset add-form widget keys."""
    keys = [
        "add_date", "add_amount", "add_type",
        "add_payment", "add_note",
        "add_category_expense", "add_category_income",
    ]
    for key in keys:
        st.session_state.pop(key, None)


def _get_categories(t_type: str) -> list[str]:
    """Return categories for the selected transaction type."""
    normalized_type = str(t_type).strip().lower()

    if normalized_type == "expense":
        return EXPENSE_CATS

    if normalized_type == "income":
        return INCOME_CATS

    raise ValueError(f"Invalid transaction type: {t_type!r}")


def _reset_add_category():
    """Reset category if the transaction type changes."""
    chosen_type = st.session_state.get("add_type", "expense")
    cats = _get_categories(chosen_type)
    category_key = f"add_category_{chosen_type}"

    if st.session_state.get(category_key) not in cats:
        st.session_state[category_key] = cats[0]


def _reset_edit_category(tx_id: int):
    """Reset the edit category when its transaction type changes."""
    type_key = f"edit_type_{tx_id}"
    chosen_type = st.session_state.get(type_key, "expense")
    cats = _get_categories(chosen_type)
    category_key = f"edit_category_{tx_id}_{chosen_type}"

    if st.session_state.get(category_key) not in cats:
        st.session_state[category_key] = cats[0]


# ── Section 1 — Add Transaction ────────────────────────────────────────────

def _section_add():
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.3rem;'>"
        "➕ Add Transaction</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0;'>"
        "All fields except Note are required.</p>",
        unsafe_allow_html=True,
    )

    # This widget must be outside the form so Streamlit reruns immediately
    # when the user changes Expense/Income.
    add_type = st.selectbox(
        "Transaction Type",
        options=VALID_TYPES,
        format_func=lambda x: x.capitalize(),
        key="add_type",
        on_change=_reset_add_category,
    )

    # Separate category keys prevent one transaction type from reusing
    # the previous type's selected category.
    cats = _get_categories(add_type)
    category_key = f"add_category_{add_type}"

    # Initialise the category key before rendering its widget.
    if st.session_state.get(category_key) not in cats:
        st.session_state[category_key] = cats[0]

    with st.form("form_add_transaction", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            add_date = st.date_input(
                "Date",
                value=date.today(),
                min_value=date(2000, 1, 1),
                max_value=date(2100, 12, 31),
                key="add_date",
            )
            add_amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                value=None,
                step=0.01,
                format="%.2f",
                placeholder="e.g. 500.00",
                key="add_amount",
            )

        with col2:
            add_category = st.selectbox(
                "Category",
                options=cats,
                key=category_key,
            )
            add_payment = st.selectbox(
                "Payment Method",
                options=PAYMENT_METHODS,
                key="add_payment",
            )
            add_note = st.text_input(
                "Note (optional)",
                max_chars=200,
                placeholder="e.g. Coffee with friends",
                key="add_note",
            )

        submitted = st.form_submit_button(
            "💾  Save Transaction",
            use_container_width=True,
        )

    if submitted:
        if add_amount is None:
            st.error(
                "⚠️ Amount is required and must be greater than 0.",
                icon="🚫",
            )
            return

        try:
            new_tx = tm.add_transaction(
                date=add_date.strftime(DATE_FMT),
                amount=add_amount,
                type=add_type.strip().lower(),
                category=add_category,
                payment_method=add_payment,
                note=add_note or "",
            )
            st.success(
                f"✅ Transaction #{new_tx['id']} saved — "
                f"{new_tx['category']} · "
                f"{_fmt_amount(new_tx['amount'])} on {new_tx['date']}",
                icon="✅",
            )
            st.session_state.pop("tx_list_cache", None)

        except ValueError as exc:
            st.error(f"⚠️ {exc}", icon="🚫")
        except Exception as exc:
            st.error(f"Unexpected error: {exc}", icon="❌")


# ── Section 2 — Filter bar ─────────────────────────────────────────────────

def _filter_bar() -> dict:
    """Render filters and return kwargs for get_transactions()."""
    with st.expander("🔍 Filter Transactions", expanded=False):
        fc1, fc2, fc3 = st.columns(3)

        with fc1:
            f_start = st.date_input(
                "From date",
                value=None,
                min_value=date(2000, 1, 1),
                max_value=date(2100, 12, 31),
                key="f_start",
            )
            f_end = st.date_input(
                "To date",
                value=None,
                min_value=date(2000, 1, 1),
                max_value=date(2100, 12, 31),
                key="f_end",
            )

        with fc2:
            f_type = st.selectbox(
                "Type",
                options=["(All)", "income", "expense"],
                format_func=lambda x: (
                    x.capitalize() if x != "(All)" else x
                ),
                key="f_type",
            )
            all_cats = ["(All)"] + sorted(
                set(EXPENSE_CATS + INCOME_CATS)
            )
            f_category = st.selectbox(
                "Category",
                options=all_cats,
                key="f_cat",
            )

        with fc3:
            f_payment = st.selectbox(
                "Payment Method",
                options=["(All)"] + PAYMENT_METHODS,
                key="f_pay",
            )
            fc3a, fc3b = st.columns(2)

            with fc3a:
                f_min = st.number_input(
                    "Min amount",
                    min_value=0.0,
                    value=None,
                    step=1.0,
                    format="%.2f",
                    key="f_min",
                )

            with fc3b:
                f_max = st.number_input(
                    "Max amount",
                    min_value=0.0,
                    value=None,
                    step=1.0,
                    format="%.2f",
                    key="f_max",
                )

        if st.button("🔄 Clear Filters", key="clear_filters"):
            for key in [
                "f_start", "f_end", "f_type", "f_cat",
                "f_pay", "f_min", "f_max",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    kwargs: dict = {}

    if f_start:
        kwargs["start_date"] = f_start.strftime(DATE_FMT)
    if f_end:
        kwargs["end_date"] = f_end.strftime(DATE_FMT)
    if f_type != "(All)":
        kwargs["type"] = f_type
    if f_category != "(All)":
        kwargs["category"] = f_category
    if f_payment != "(All)":
        kwargs["payment_method"] = f_payment
    if f_min is not None:
        kwargs["min_amount"] = f_min
    if f_max is not None:
        kwargs["max_amount"] = f_max

    return kwargs


# ── Section 3 — Transaction list ───────────────────────────────────────────

def _section_list():
    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.3rem;'>"
        "📋 All Transactions</h3>",
        unsafe_allow_html=True,
    )

    filter_kwargs = _filter_bar()

    try:
        transactions = tm.get_transactions(**filter_kwargs)
    except ValueError as exc:
        st.error(f"⚠️ Filter error: {exc}", icon="🚫")
        return
    except Exception as exc:
        st.error(f"Could not load transactions: {exc}", icon="❌")
        return

    if not transactions:
        st.info(
            "No transactions found. Try adjusting the filters or add one above.",
            icon="ℹ️",
        )
        return

    total_income = sum(
        t["amount"] for t in transactions if t.get("type") == "income"
    )
    total_expense = sum(
        t["amount"] for t in transactions if t.get("type") == "expense"
    )
    net = total_income - total_expense

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("📦 Transactions", len(transactions))
    mc2.metric("▲ Income", _fmt_amount(total_income))
    mc3.metric("▼ Expenses", _fmt_amount(total_expense))
    mc4.metric(
        "💰 Net",
        _fmt_amount(abs(net)),
        delta=f"{'▲' if net >= 0 else '▼'} "
              f"{'surplus' if net >= 0 else 'deficit'}",
        delta_color="normal" if net >= 0 else "inverse",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    df = pd.DataFrame(transactions)
    display_cols = [
        "id", "date", "type", "category",
        "payment_method", "amount", "note",
    ]
    df = df[[c for c in display_cols if c in df.columns]]
    df = df.rename(columns={
        "id": "ID",
        "date": "Date",
        "type": "Type",
        "category": "Category",
        "payment_method": "Payment",
        "amount": "Amount (₹)",
        "note": "Note",
    })
    df["Amount (₹)"] = df["Amount (₹)"].apply(
        lambda x: f"{x:,.2f}"
    )
    df["Type"] = df["Type"].str.capitalize()
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Date": st.column_config.TextColumn("Date", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Category": st.column_config.TextColumn(
                "Category", width="medium"
            ),
            "Payment": st.column_config.TextColumn(
                "Payment", width="medium"
            ),
            "Amount (₹)": st.column_config.TextColumn(
                "Amount (₹)", width="medium"
            ),
            "Note": st.column_config.TextColumn("Note", width="large"),
        },
    )

    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; font-size:0.85rem; "
        "margin-top:0.8rem;'>"
        "Select a transaction below to edit or delete it.</p>",
        unsafe_allow_html=True,
    )

    tx_map = {
        f"#{t['id']}  {t['date']}  ·  "
        f"{t['type'].capitalize()}  ·  "
        f"{t['category']}  ·  ₹{t['amount']:,.2f}": t
        for t in sorted(
            transactions,
            key=lambda x: x["date"],
            reverse=True,
        )
    }

    selected_label = st.selectbox(
        "Select transaction",
        options=["— choose one —"] + list(tx_map.keys()),
        key="tx_select",
        label_visibility="collapsed",
    )

    if selected_label == "— choose one —":
        return

    selected_tx = tx_map[selected_label]
    tx_id = selected_tx["id"]
    badge = _type_badge(selected_tx["type"])

    note_html = ""
    if selected_tx.get("note"):
        note_html = (
            f"<div style='margin-top:0.4rem; color:{TEXT_SECONDARY};'>"
            f"📝 {selected_tx['note']}</div>"
        )

    amount_color = (
        "#6EE7B7"
        if selected_tx["type"] == "income"
        else "#F87171"
    )

    st.markdown(
        f"""
        <div class="sw-card" style="margin-top:0.8rem;">
            <div style="display:flex; justify-content:space-between;
                        align-items:center;">
                <span style="color:{LAV_100}; font-size:1.1rem;
                             font-weight:700;">
                    #{tx_id} &nbsp;·&nbsp; {selected_tx['category']}
                </span>
                {badge}
            </div>
            <div style="margin-top:0.6rem; display:grid;
                        grid-template-columns:1fr 1fr 1fr; gap:0.4rem;">
                <span style="color:{TEXT_SECONDARY};">
                    📅 {selected_tx['date']}
                </span>
                <span style="color:{TEXT_SECONDARY};">
                    💳 {selected_tx['payment_method']}
                </span>
                <span style="color:{amount_color}; font-weight:700;">
                    ₹{selected_tx['amount']:,.2f}
                </span>
            </div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    act_col1, act_col2, _ = st.columns([1, 1, 4])

    with act_col1:
        if st.button(
            "✏️ Edit",
            key=f"edit_btn_{tx_id}",
            use_container_width=True,
        ):
            st.session_state["editing_tx_id"] = tx_id
            st.session_state["active_tab"] = "edit"
            st.rerun()

    with act_col2:
        if st.button(
            "🗑️ Delete",
            key=f"del_btn_{tx_id}",
            use_container_width=True,
        ):
            st.session_state["pending_delete_id"] = tx_id
            st.rerun()

    if st.session_state.get("pending_delete_id") == tx_id:
        st.warning(
            f"⚠️ Are you sure you want to delete transaction **#{tx_id}**? "
            "This cannot be undone.",
            icon="⚠️",
        )
        dc1, dc2, _ = st.columns([1, 1, 4])

        with dc1:
            if st.button(
                "✅ Yes, delete",
                key=f"confirm_del_{tx_id}",
                use_container_width=True,
            ):
                try:
                    tm.delete_transaction(tx_id)
                    st.success(f"Transaction #{tx_id} deleted.", icon="✅")
                    st.session_state.pop("pending_delete_id", None)
                    st.session_state.pop("tx_select", None)
                    st.rerun()
                except ValueError as exc:
                    st.error(f"⚠️ {exc}", icon="🚫")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}", icon="❌")

        with dc2:
            if st.button(
                "❌ Cancel",
                key=f"cancel_del_{tx_id}",
                use_container_width=True,
            ):
                st.session_state.pop("pending_delete_id", None)
                st.rerun()


# ── Section 4 — Edit Transaction ───────────────────────────────────────────

def _section_edit():
    tx_id = st.session_state.get("editing_tx_id")

    if tx_id is None:
        st.info(
            "No transaction selected for editing. "
            "Go to **All Transactions**, select a row, and press ✏️ Edit.",
            icon="ℹ️",
        )
        return

    try:
        current = tm.get_transaction_by_id(tx_id)
    except ValueError as exc:
        st.error(f"⚠️ {exc}", icon="🚫")
        st.session_state.pop("editing_tx_id", None)
        return

    st.markdown(
        f"<h3 style='color:{LAV_200}; margin-bottom:0.3rem;'>"
        f"✏️ Editing Transaction #{tx_id}</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0;'>"
        "Modify any field and click Save. "
        "Leave a field unchanged to keep its current value.</p>",
        unsafe_allow_html=True,
    )

    try:
        current_date = datetime.strptime(
            current["date"], DATE_FMT
        ).date()
    except Exception:
        current_date = date.today()

    current_type = current.get("type", "expense")

    # Unique type key per transaction. The selector is outside the form
    # so changing its value triggers a rerun immediately.
    type_key = f"edit_type_{tx_id}"
    edit_type = st.selectbox(
        "Transaction Type",
        options=VALID_TYPES,
        index=VALID_TYPES.index(current_type),
        format_func=lambda x: x.capitalize(),
        key=type_key,
        on_change=lambda: _reset_edit_category(tx_id),
    )

    cats_edit = _get_categories(edit_type)
    category_key = f"edit_category_{tx_id}_{edit_type}"

    if st.session_state.get(category_key) not in cats_edit:
        if current.get("category") in cats_edit:
            st.session_state[category_key] = current["category"]
        else:
            st.session_state[category_key] = cats_edit[0]

    with st.form(f"form_edit_transaction_{tx_id}", clear_on_submit=False):
        ec1, ec2 = st.columns(2)

        with ec1:
            edit_date = st.date_input(
                "Date",
                value=current_date,
                min_value=date(2000, 1, 1),
                max_value=date(2100, 12, 31),
                key=f"edit_date_{tx_id}",
            )
            edit_amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                value=float(current["amount"]),
                step=0.01,
                format="%.2f",
                key=f"edit_amount_{tx_id}",
            )

        with ec2:
            edit_category = st.selectbox(
                "Category",
                options=cats_edit,
                key=category_key,
            )
            edit_payment = st.selectbox(
                "Payment Method",
                options=PAYMENT_METHODS,
                index=(
                    PAYMENT_METHODS.index(current["payment_method"])
                    if current["payment_method"] in PAYMENT_METHODS
                    else 0
                ),
                key=f"edit_payment_{tx_id}",
            )
            edit_note = st.text_input(
                "Note (optional)",
                value=current.get("note", ""),
                max_chars=200,
                key=f"edit_note_{tx_id}",
            )

        scol1, scol2 = st.columns(2)

        with scol1:
            save_clicked = st.form_submit_button(
                "💾 Save Changes",
                use_container_width=True,
            )

        with scol2:
            cancel_clicked = st.form_submit_button(
                "✖ Cancel",
                use_container_width=True,
            )

    if cancel_clicked:
        st.session_state.pop("editing_tx_id", None)
        st.session_state["active_tab"] = "list"
        st.rerun()

    if save_clicked:
        try:
            updated = tm.update_transaction(
                tx_id,
                date=edit_date.strftime(DATE_FMT),
                amount=edit_amount,
                type=edit_type,
                category=edit_category,
                payment_method=edit_payment,
                note=edit_note or "",
            )
            st.success(
                f"✅ Transaction #{updated['id']} updated — "
                f"{updated['category']} · "
                f"{_fmt_amount(updated['amount'])} on {updated['date']}",
                icon="✅",
            )
            st.session_state.pop("editing_tx_id", None)
            st.session_state["active_tab"] = "list"
            st.rerun()

        except ValueError as exc:
            st.error(f"⚠️ {exc}", icon="🚫")
        except Exception as exc:
            st.error(f"Unexpected error: {exc}", icon="❌")


# ── Main render ────────────────────────────────────────────────────────────

def render():
    st.markdown(
        f"<h1 style='color:{LAV_100}; margin-bottom:0.1rem;'>"
        "💳 Transactions</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY}; margin-top:0; "
        "margin-bottom:1.4rem;'>"
        "Manage your income and expenses.</p>",
        unsafe_allow_html=True,
    )

    tab_add, tab_list, tab_edit = st.tabs([
        "➕ Add Transaction",
        "📋 All Transactions",
        "✏️ Edit Transaction",
    ])

    with tab_add:
        _section_add()

    with tab_list:
        _section_list()

    with tab_edit:
        _section_edit()
