import os
import time
from typing import List, Tuple


def find_unused_files(folder: str, days: int = 90) -> List[str]:

    unused_files: List[str] = []
    current_time = time.time()

    limit = days * 24 * 60 * 60

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)

            try:
                last_access = os.path.getatime(path)
                if current_time - last_access > limit:
                    unused_files.append(path)
            except OSError:
                # Skip files where access time is not available
                continue

    return unused_files


def detect_usage(
    folder: str,
    unused_days: int = 90,
    rarely_used_days: int = 30,
) -> Tuple[List[str], List[str]]:
    current_time = time.time()
    unused_limit = unused_days * 24 * 60 * 60
    rarely_limit = rarely_used_days * 24 * 60 * 60

    unused_files: List[str] = []
    rarely_used_files: List[str] = []

    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    downloads_path = os.path.abspath(downloads_path)
    downloads_exists = os.path.exists(downloads_path)

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)

            try:
                last_access = os.path.getatime(path)
            except OSError:
                # Skip files without reliable access time metadata
                continue

            age = current_time - last_access

            in_downloads = False
            if downloads_exists:
                try:
                    in_downloads = os.path.commonpath(
                        [downloads_path, os.path.abspath(path)]
                    ) == downloads_path
                except ValueError:
                    # Paths on different drives (Windows) – treat as not in Downloads
                    in_downloads = False

            if age > unused_limit:
                unused_files.append(path)
            elif age > rarely_limit or in_downloads:
                rarely_used_files.append(path)

    return unused_files, rarely_used_files

