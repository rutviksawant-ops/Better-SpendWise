"""
backend_bridge.py
=================
Puts SW_Backend on sys.path so that transaction_manager.py can import
data_manager.py the same way it does when run directly from the backend folder.

Import this module once (from app.py or any page) before touching anything
in transaction_manager. It is idempotent — safe to import multiple times.
"""

import sys
import os

_BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "SW_Backend")
)

if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Re-export the public API so pages can write:
#   from backend_bridge import tm
# and call tm.add_transaction(...) etc.
import transaction_manager as tm  # noqa: E402

__all__ = ["tm"]
