"""
Drishyamitra - Person Naming Engine
Adapted from FileMind naming_engine.py
Instead of AI-generated folder labels from text, this manages person naming:
  - Returns default "Person_N" labels until user names them
  - Supports user-triggered renaming
"""

# In-memory name overrides (user-assigned names)
# Persisted through storage.py in cluster_engine
_person_names = {}


def get_person_label(person_id):
    """
    Get a display label for a person.
    Returns user-assigned name if available, otherwise default "Person_N".
    
    Args:
        person_id: Person identifier string (e.g., "person_0")
    
    Returns:
        str: Person display name
    """
    if person_id in _person_names:
        return _person_names[person_id]

    # Extract number from person_id for cleaner default names
    try:
        num = int(person_id.split("_")[-1]) + 1
        return f"Person_{num}"
    except (ValueError, IndexError):
        return person_id


def set_person_name(person_id, name):
    """
    Set a user-assigned name for a person.
    
    Args:
        person_id: Person identifier string
        name: User-provided name
    
    Returns:
        str: The sanitized name that was set
    """
    # Sanitize name
    clean_name = name.strip()
    if not clean_name:
        clean_name = get_person_label(person_id)

    _person_names[person_id] = clean_name
    print(f"Naming Engine: Person '{person_id}' named as '{clean_name}'")
    return clean_name


def load_names_from_storage(storage):
    """
    Sync in-memory names from persisted storage.
    Called on startup to restore user-assigned names.
    
    Args:
        storage: The storage dict from storage.py
    """
    global _person_names
    for person_id, person_data in storage.items():
        name = person_data.get("name", "")
        if name and not name.startswith("Person_"):
            _person_names[person_id] = name


def get_all_names():
    """Return all user-assigned names."""
    return dict(_person_names)
