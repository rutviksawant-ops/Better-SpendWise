"""
Import verification test for SW_Frontend pages and SW_Backend modules.
Run from SW_Frontend directory.
"""
import sys, os
sys.path.insert(0, os.path.abspath('../SW_Backend'))

# ── Backend modules ──────────────────────────────────────────────────────
import budget_manager as bm
import analytics_engine as ae
import transaction_manager as tm
print('Backend imports: OK')

b = bm.load_budgets()
print('  bm.load_budgets:', b)
s = ae.summary([])
print('  ae.summary (empty list):', s)
cb = ae.category_breakdown([])
print('  ae.category_breakdown (empty):', cb)
mt = ae.monthly_trend([])
print('  ae.monthly_trend (empty):', mt)
ive = ae.income_vs_expense_monthly([])
print('  ae.income_vs_expense_monthly (empty):', ive)
al = ae.unusual_spending_alerts([])
print('  ae.unusual_spending_alerts (empty):', al)
rec = ae.recent_transactions([])
print('  ae.recent_transactions (empty):', rec)

real = tm.get_transactions()
print('Real transactions count:', len(real), '(unchanged)')
for t in real:
    tid = t['id']
    tdate = t['date']
    ttype = t['type']
    tamt  = t['amount']
    print(f'  id={tid} date={tdate} type={ttype} amount={tamt}')

# ── Mock Streamlit to allow page module imports without running a server ─
import unittest.mock as mock
sys.modules['streamlit'] = mock.MagicMock()
sys.modules['plotly'] = mock.MagicMock()
sys.modules['plotly.graph_objects'] = mock.MagicMock()
sys.modules['plotly.express'] = mock.MagicMock()
sys.modules['pandas'] = mock.MagicMock()

import importlib
errors = []
for page_name in ['dashboard', 'budgets', 'analytics', 'transactions']:
    try:
        mod = importlib.import_module(f'pages.{page_name}')
        print(f'  pages.{page_name}: imported OK, render={callable(getattr(mod, "render", None))}')
    except Exception as e:
        print(f'  pages.{page_name}: IMPORT ERROR -> {e}')
        errors.append(page_name)

# Also verify backend_bridge
try:
    import backend_bridge
    print('  backend_bridge: imported OK')
except Exception as e:
    print(f'  backend_bridge: ERROR -> {e}')
    errors.append('backend_bridge')

print()
if errors:
    print('FAILED:', errors)
    sys.exit(1)
else:
    print('All imports verified successfully.')
