"""
data_manager.py
===============

File I/O layer for the SpendWise backend.

Responsibility:
    Read and write the list of transaction dictionaries to a local JSON file,
    safely. This module knows nothing about validation, budgets or analytics;
    it only persists whatever list it is given.

Public API:
    load_data()              -> list[dict]
    save_data(transactions)  -> None

Storage location:
    <folder containing this file>/data/transactions.json
"""

import json
import os
import tempfile

# ---------------------------------------------------------------------------
# File location
# ---------------------------------------------------------------------------
# The path is anchored to this file's own folder (not the current working
# directory), so the app behaves the same no matter where it is launched from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "transactions.json")


def _ensure_data_dir() -> None:
    """Create the data directory if it does not already exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_data(transactions: list) -> None:
    """
    Write the list of transaction dictionaries to the JSON file.

    The write is atomic: data is first written to a temporary file in the
    same directory and then moved over the real file with os.replace(). If
    the program crashes mid-write, the previous valid file is left intact
    instead of being truncated or half-written.

    Args:
        transactions: A list of transaction dictionaries.

    Raises:
        TypeError: If `transactions` is not a list.
        OSError:   If the file cannot be written.
    """
    if not isinstance(transactions, list):
        raise TypeError("transactions must be a list of dictionaries.")

    _ensure_data_dir()

    # Create the temp file in the same folder so os.replace() stays on one
    # filesystem (a requirement for the replace to be atomic).
    fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(transactions, temp_file, indent=4, ensure_ascii=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # force the bytes onto disk
        os.replace(temp_path, DATA_FILE)
    except Exception:
        # Clean up the temp file if anything went wrong, then re-raise.
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def load_data() -> list:
    """
    Read and parse the JSON file.

    Self-healing behaviour: if the file is missing, empty, contains invalid
    JSON, or contains valid JSON that is not a list, this function recreates
    a valid empty JSON file ("[]") and returns an empty list.

    Returns:
        A list of transaction dictionaries (possibly empty).
    """
    _ensure_data_dir()

    # Case 1: file does not exist yet -> create it.
    if not os.path.exists(DATA_FILE):
        save_data([])
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as data_file:
            content = data_file.read()

        # Case 2: file exists but is empty or only whitespace.
        if not content.strip():
            save_data([])
            return []

        data = json.loads(content)

        # Case 3: valid JSON, but not the structure we expect.
        if not isinstance(data, list):
            save_data([])
            return []

        return data

    except (json.JSONDecodeError, UnicodeDecodeError):
        # Case 4: corrupted file -> reset to a valid empty list.
        save_data([])
        return []
    except OSError:
        # Case 5: file could not be read (e.g. permissions). Try to recreate
        # it; if even that fails, the OSError from save_data() propagates so
        # the caller learns that storage is genuinely unusable.
        save_data([])
        return []
