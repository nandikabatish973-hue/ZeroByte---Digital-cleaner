import json
import os
import re
from typing import Dict, List, Any


PREFERENCES_FILE = os.path.join(
    os.path.dirname(__file__), "personalization_prefs.json"
)


def _default_preferences() -> Dict[str, Any]:
    return {"rules": []}


def load_preferences() -> Dict[str, Any]:
    """
    Load personalization rules from disk.
    """
    if not os.path.exists(PREFERENCES_FILE):
        return _default_preferences()

    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "rules" not in data or not isinstance(data["rules"], list):
                return _default_preferences()
            return data
    except (json.JSONDecodeError, OSError):
        return _default_preferences()


def save_preferences(prefs: Dict[str, Any]) -> None:
    """
    Persist personalization rules to disk.
    """
    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
    except OSError:
        # If we cannot save, silently ignore – the app should still function
        pass


def _build_rules_from_example(file_path: str, label: str) -> List[Dict[str, str]]:

    rules: List[Dict[str, str]] = []

    basename = os.path.basename(file_path).lower()
    ext = os.path.splitext(basename)[1]
    folder_name = os.path.basename(os.path.dirname(file_path)).lower()

    if ext:
        rules.append({"type": "extension", "value": ext, "label": label})

    tokens = [t for t in re.split(r"[^a-z0-9]+", basename) if len(t) >= 4]
    for token in tokens[:3]:
        rules.append({"type": "keyword", "value": token, "label": label})

    if folder_name:
        rules.append({"type": "folder", "value": folder_name, "label": label})

    return rules


def update_preferences(file_path: str, new_label: str) -> Dict[str, Any]:
    
    prefs = load_preferences()
    prefs.setdefault("rules", [])

    new_rules = _build_rules_from_example(file_path, new_label)

    for rule in new_rules:
        existing = next(
            (
                r
                for r in prefs["rules"]
                if r.get("type") == rule["type"] and r.get("value") == rule["value"]
            ),
            None,
        )
        if existing:
            existing["label"] = rule["label"]
        else:
            prefs["rules"].append(rule)

    save_preferences(prefs)
    return prefs


def apply_preferences(
    file_path: str, base_label: str, prefs: Dict[str, Any] | None = None
) -> str:

    if prefs is None:
        prefs = load_preferences()

    rules = prefs.get("rules", [])
    if not rules:
        return base_label

    basename = os.path.basename(file_path).lower()
    ext = os.path.splitext(basename)[1]
    folder_name = os.path.basename(os.path.dirname(file_path)).lower()

    label = base_label

    for rule in rules:
        r_type = rule.get("type")
        value = rule.get("value", "")
        target_label = rule.get("label", label)

        if r_type == "extension" and ext == value:
            label = target_label
        elif r_type == "keyword" and value in basename:
            label = target_label
        elif r_type == "folder" and folder_name == value:
            label = target_label

    return label

