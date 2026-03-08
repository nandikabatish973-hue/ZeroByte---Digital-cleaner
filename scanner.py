import os
import time

def scan_folder(folder_path):
    total_files = 0
    total_size = 0

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)

    return total_files, total_size


def get_recent_file(folder):
    latest_time = 0
    latest_file = ""

    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                access_time = os.path.getatime(path)

                if access_time > latest_time:
                    latest_time = access_time
                    latest_file = path
            except:
                pass

    return latest_file