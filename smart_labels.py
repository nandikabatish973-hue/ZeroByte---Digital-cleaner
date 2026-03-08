import os
from collections import Counter
from typing import Dict, List, Tuple

from personalization import load_preferences, apply_preferences


PERSONAL_EXT = {".jpg", ".jpeg", ".png", ".mp4", ".mov", ".gif"}
WORK_EXT = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".py", ".ipynb"}
TEMP_EXT = {".zip", ".rar", ".exe", ".tmp", ".iso"}

PERSONAL_KEYWORDS = {
    "photo",
    "pic",
    "selfie",
    "vacation",
    "holiday",
    "family",
    "birthday",
}
WORK_KEYWORDS = {
    "report",
    "invoice",
    "resume",
    "cv",
    "presentation",
    "slides",
    "meeting",
    "notes",
    "project",
}
TEMP_KEYWORDS = {
    "setup",
    "installer",
    "temp",
    "cache",
    "backup",
    "copy",
    "old",
}


def get_label(file_path: str) -> str:
    name = os.path.basename(file_path).lower()
    ext = os.path.splitext(name)[1]
    folder_path = os.path.dirname(file_path).lower()

    if ext in PERSONAL_EXT:
        return "Personal"
    if ext in TEMP_EXT:
        return "Temporary"
    if ext in WORK_EXT:
        return "Work"

    if any(k in name for k in PERSONAL_KEYWORDS) or any(
        k in folder_path for k in ["photos", "pictures", "camera", "gallery"]
    ):
        return "Personal"

    if any(k in name for k in TEMP_KEYWORDS) or any(
        k in folder_path for k in ["temp", "cache", "downloads"]
    ):
        return "Temporary"

    if any(k in name for k in WORK_KEYWORDS) or any(
        k in folder_path for k in ["documents", "work", "projects"]
    ):
        return "Work"

    return "Unknown"


def label_files(
    folder: str,
) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    prefs = load_preferences()
    labeled: List[Dict[str, str]] = []
    counts: Counter = Counter()

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)

            base_label = get_label(path)
            final_label = apply_preferences(path, base_label, prefs)

            labeled.append(
                {
                    "name": file,
                    "path": path,
                    "base_label": base_label,
                    "label": final_label,
                }
            )
            counts[final_label] += 1

    return labeled, dict(counts)

