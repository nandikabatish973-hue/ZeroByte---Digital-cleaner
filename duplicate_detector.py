import hashlib
import os
from collections import defaultdict
from typing import Dict, List, Tuple


def get_file_hash(file_path: str) -> str:
    hasher = hashlib.md5()

    with open(file_path, "rb") as file:
        buf = file.read()
        hasher.update(buf)

    return hasher.hexdigest()


def find_duplicates(folder: str) -> List[str]:

    hashes: Dict[str, str] = {}
    duplicates: List[str] = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            file_hash = get_file_hash(path)

            if file_hash in hashes:
                duplicates.append(path)
            else:
                hashes[file_hash] = path

    return duplicates


def find_duplicate_groups(folder: str) -> List[List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            file_hash = get_file_hash(path)
            groups[file_hash].append(path)

    return [paths for paths in groups.values() if len(paths) > 1]


def summarize_duplicate_stats(
    duplicate_groups: List[List[str]],
) -> Tuple[int, int, int]:
    total_files = 0
    total_size = 0
    potential_savings = 0

    for group in duplicate_groups:
        if not group:
            continue
        total_files += len(group)

        try:
            base_size = os.path.getsize(group[0])
        except OSError:
            base_size = 0

        group_size = 0
        for path in group:
            try:
                group_size += os.path.getsize(path)
            except OSError:
                continue

        total_size += group_size

        if base_size > 0:
            potential_savings += base_size * (len(group) - 1)

    return total_files, total_size, potential_savings
