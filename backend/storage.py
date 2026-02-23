"""
Drishyamitra - JSON Storage Layer
Adapted from FileMind storage.py
Persists face data, person groupings, and photo metadata to JSON.
"""

import json
import os
from config import STORAGE_FILE


def load_storage():
    """Load face/person data from JSON file."""
    if not os.path.exists(STORAGE_FILE):
        return {}

    try:
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Storage load error: {e}")
        return {}


def save_storage(data):
    """Save face/person data to JSON file."""
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Storage save error: {e}")
