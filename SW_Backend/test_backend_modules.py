"""
test_backend_modules.py
=======================
Non-destructive tests for budget_manager and analytics_engine.

Strategy:
- Save original budget state before any mutation.
- Run all tests.
- Restore original budget state when done.
- Never touch transactions.json.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import budget_manager as bm
import analytics_engine as ae
import transaction_manager as tm

PASS = 0
FAIL = 0

def check(label, condition, got=None):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}  (got: {got!r})")
        FAIL += 1

print("=" * 60)
print("SpendWise Backend Unit Tests")
print("=" * 60)

# ── Save original budget state ──────────────────────────────────────────────
original_budgets = bm.load_budgets()
print(f"\n[Setup] Original budgets saved: {original_budgets}\n")

try:
    # ── budget_manager tests ───────────────────────────────────────────────
    print("--- budget_manager ---")

    # 1. load returns a dict with correct keys
    b = bm.load_budgets()
    check("load_budgets returns dict with 'overall' and 'categories'",
          isinstance(b, dict) and "overall" in b and "categories" in b)

    # 2. set_overall_budget
    b = bm.set_overall_budget(10000)
    check("set_overall_budget(10000) stores 10000.0",
          b["overall"] == 10000.0, b["overall"])

    # 3. set_category_budget
    bm.set_category_budget("Food", 2000)
    bm.set_category_budget("Transport", 500)
    b = bm.load_budgets()
    check("set_category_budget stores Food=2000",
          b["categories"].get("Food") == 2000.0, b["categories"])
    check("set_category_budget stores Transport=500",
          b["categories"].get("Transport") == 500.0, b["categories"])

    # 4. remove_category_budget
    bm.remove_category_budget("Transport")
    b = bm.load_budgets()
    check("remove_category_budget removes Transport",
          "Transport" not in b["categories"], b["categories"])

    # 5. set_category_budget with 0 removes category
    bm.set_category_budget("Food", 0)
    b = bm.load_budgets()
    check("set_category_budget(cat, 0) removes that category",
          "Food" not in b["categories"], b["categories"])

    # 6. Negative budget rejected
    rejected = False
    try:
        bm.set_overall_budget(-100)
    except ValueError:
        rejected = True
    check("set_overall_budget(-100) raises ValueError", rejected)

    # 7. Non-numeric budget rejected
    rejected2 = False
    try:
        bm.set_overall_budget("a lot")
    except ValueError:
        rejected2 = True
    check("set_overall_budget('a lot') raises ValueError", rejected2)

    # 8. get_budget_status with synthetic transactions
    bm.set_overall_budget(10000)
    bm.set_category_budget("Food", 3000)
    synthetic_txns = [
        {"id": 99, "date": "2026-10-15", "type": "expense", "category": "Food",
         "amount": 1500.0, "payment_method": "UPI", "note": "test"},
        {"id": 100, "date": "2026-10-16", "type": "expense", "category": "Transport",
         "amount": 200.0, "payment_method": "Cash", "note": "test"},
        {"id": 101, "date": "2026-09-10", "type": "expense", "category": "Food",
         "amount": 999.0, "payment_method": "UPI", "note": "prior month - should be excluded"},
        {"id": 102, "date": "2026-10-17", "type": "income", "category": "Salary",
         "amount": 5000.0, "payment_method": "Bank Transfer", "note": "test income - excluded from expense sum"},
    ]
    status = bm.get_budget_status(synthetic_txns, 2026, 10)
    check("get_budget_status: overall spent = 1700 (food+transport, income excluded)",
          status["overall"]["spent"] == 1700.0, status["overall"]["spent"])
    check("get_budget_status: overall remaining = 8300",
          status["overall"]["remaining"] == 8300.0, status["overall"]["remaining"])
    check("get_budget_status: Food pct_used = 50.0",
          status["categories"]["Food"]["pct_used"] == 50.0,
          status["categories"]["Food"]["pct_used"])
    check("get_budget_status: prior month transaction excluded",
          status["overall"]["spent"] != 2699.0, status["overall"]["spent"])
    check("get_budget_status: Transport in unbudgeted (no budget set)",
          "Transport" in status["unbudgeted_spend"], status["unbudgeted_spend"])
    check("get_budget_status: income excluded from unbudgeted",
          "Salary" not in status["unbudgeted_spend"], status["unbudgeted_spend"])

    # 9. Warning levels
    bm.set_category_budget("Food", 1600)  # 1500 spent -> 93.75%
    status2 = bm.get_budget_status(synthetic_txns, 2026, 10)
    check("Warning level 'danger' at ~94% used",
          status2["categories"]["Food"]["level"] == "danger",
          status2["categories"]["Food"])

    bm.set_category_budget("Food", 1400)  # 1500 spent > 1400 budget
    status3 = bm.get_budget_status(synthetic_txns, 2026, 10)
    check("Warning level 'exceeded' when spent > budget",
          status3["categories"]["Food"]["level"] == "exceeded",
          status3["categories"]["Food"])
    check("exceeded_by is correct",
          status3["categories"]["Food"]["exceeded_by"] == 100.0,
          status3["categories"]["Food"]["exceeded_by"])

    # 10. daily_allowance
    da = bm.daily_allowance(900, 9)
    check("daily_allowance(900, 9) = 100.0", da == 100.0, da)
    check("daily_allowance(0, 9) = 0.0", bm.daily_allowance(0, 9) == 0.0)
    check("daily_allowance(900, 0) = 0.0", bm.daily_allowance(900, 0) == 0.0)

    # ── analytics_engine tests ─────────────────────────────────────────────
    print("\n--- analytics_engine ---")

    ana_txns = [
        {"id": 1, "date": "2026-09-05", "type": "income",  "category": "Salary",    "amount": 8000.0},
        {"id": 2, "date": "2026-09-10", "type": "expense", "category": "Food",      "amount": 500.0},
        {"id": 3, "date": "2026-09-15", "type": "expense", "category": "Transport", "amount": 200.0},
        {"id": 4, "date": "2026-10-02", "type": "income",  "category": "Salary",    "amount": 8000.0},
        {"id": 5, "date": "2026-10-10", "type": "expense", "category": "Food",      "amount": 600.0},
        {"id": 6, "date": "2026-10-12", "type": "expense", "category": "Food",      "amount": 550.0},
        {"id": 7, "date": "2026-10-18", "type": "expense", "category": "Food",      "amount": 8000.0},  # unusual
        {"id": 8, "date": "2026-10-20", "type": "expense", "category": "Transport", "amount": 150.0},
    ]

    # 11. summary
    s = ae.summary(ana_txns)
    check("summary total_income = 16000",  s["total_income"]  == 16000.0, s)
    check("summary total_expense = 10000", s["total_expense"] == 10000.0, s)
    check("summary net = 6000",            s["net"]           == 6000.0,  s)
    check("summary savings_rate = 37.5",   s["savings_rate"]  == 37.5,    s)

    # 12. summary with date range
    s_oct = ae.summary(ana_txns, start_date="2026-10-01", end_date="2026-10-31")
    check("summary filtered to Oct: income = 8000",  s_oct["total_income"]  == 8000.0,  s_oct)
    check("summary filtered to Oct: expense = 9300", s_oct["total_expense"] == 9300.0,  s_oct)

    # 13. savings_rate edge cases
    check("savings_rate(0, 500) = None",                ae.savings_rate(0, 500) is None)
    check("savings_rate(10000, 2000) = 80.0",           ae.savings_rate(10000, 2000) == 80.0)
    check("savings_rate negative when over-spending",   ae.savings_rate(1000, 1500) < 0)

    # 14. category_breakdown
    cb = ae.category_breakdown(ana_txns, "expense")
    check("category_breakdown Food is largest",
          list(cb.keys())[0] == "Food", cb)
    check("category_breakdown Food total = 9650 (500+600+550+8000)",
          cb["Food"] == 9650.0, cb)

    # 15. monthly_trend
    mt = ae.monthly_trend(ana_txns, "expense")
    check("monthly_trend has 2 months", len(mt) == 2, mt)
    check("monthly_trend Sept expense = 700", mt[0]["amount"] == 700.0, mt)

    # 16. income_vs_expense_monthly
    ive = ae.income_vs_expense_monthly(ana_txns)
    check("income_vs_expense has 2 months", len(ive) == 2, ive)
    check("October net = -1300 (8000 - 9300)", ive[1]["net"] == -1300.0, ive[1])

    # 17. recent_transactions
    rec = ae.recent_transactions(ana_txns, 3)
    check("recent_transactions returns 3",       len(rec) == 3, rec)
    check("recent_transactions newest first",    rec[0]["id"] == 8, rec[0])

    # 18. unusual_spending_alerts — absolute rule
    alerts = ae.unusual_spending_alerts(ana_txns, abs_threshold=5000, relative_multiplier=2.5, min_history_count=3)
    ids_flagged = {a["tx_id"] for a in alerts}
    check("Alert: tx 7 (Food 8000) flagged by absolute rule (>5000)",
          7 in ids_flagged, alerts)

    # 19. unusual_spending_alerts — relative rule
    # Food avg of tx 2,5,6 = (500+600+550)/3 = 550; tx 7 = 8000 = 14.5x > 2.5x threshold
    food_alerts = [a for a in alerts if a["category"] == "Food"]
    check("At least one Food alert exists", len(food_alerts) > 0, food_alerts)
    check("Alert reason is a non-empty string", isinstance(food_alerts[0]["reason"], str) and len(food_alerts[0]["reason"]) > 0, food_alerts[0])

    # 20. No alerts for normal amounts (threshold very high)
    no_alerts = ae.unusual_spending_alerts(ana_txns, abs_threshold=999999, relative_multiplier=999)
    check("No alerts when thresholds are very high", len(no_alerts) == 0, no_alerts)

    # ── Real data smoke test (read-only) ───────────────────────────────────
    print("\n--- Real transaction data (read-only) ---")
    real = tm.get_transactions()
    print(f"  Real transaction count: {len(real)}")
    rs = ae.summary(real)
    print(f"  Summary: income={rs['total_income']}, expense={rs['total_expense']}, net={rs['net']}")
    real_alerts = ae.unusual_spending_alerts(real, abs_threshold=1000)
    print(f"  Unusual alerts (abs > 1000): {len(real_alerts)}")
    real_status = bm.get_budget_status(real, 2026, 10)
    print(f"  Budget status overall: {real_status['overall']}")
    check("Real data summary runs without error", True)

finally:
    # ── Restore original budget state ──────────────────────────────────────
    bm.save_budgets(original_budgets)
    restored = bm.load_budgets()
    print(f"\n[Teardown] Budgets restored to: {restored}")

print()
print("=" * 60)
print(f"Results: {PASS} passed, {FAIL} failed")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
