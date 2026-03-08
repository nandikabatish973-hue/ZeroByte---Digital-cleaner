def calculate_carbon(size_bytes):

    size_gb = size_bytes/(1024**3)

    carbon = size_gb * 0.04

    return size_gb, carbon

