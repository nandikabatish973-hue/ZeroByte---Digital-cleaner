import os
import time
from typing import List


def find_old_files(folder: str, months: int = 12) -> List[str]:
    old_files: List[str] = []

    current_time = time.time()
    limit = months * 30 * 24 * 60 * 60

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)

            try:
                last_access = os.path.getatime(path)
                if current_time - last_access > limit:
                    old_files.append(path)
            except OSError:
                continue

    return old_files


def find_old_files_by_days(folder: str, days: int) -> List[str]:
    old_files: List[str] = []
    current_time = time.time()
    limit = days * 24 * 60 * 60

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)

            try:
                last_access = os.path.getatime(path)
                if current_time - last_access > limit:
                    old_files.append(path)
            except OSError:
                continue

    return old_files
