#! python3
from datetime import datetime


def get_month_time_str(t: datetime) -> str:
    return t.strftime('%y-%m')
