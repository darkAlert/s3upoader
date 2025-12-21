"""
© AVA, 2025
"""
from datetime import datetime


def get_unique_id():
    return int(datetime.now().timestamp() * 100000000)
