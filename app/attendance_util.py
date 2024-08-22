from typing import Tuple
from datetime import datetime

from flask import session


def get_month_workday(selected_date: str = "") -> Tuple[int, int, str]:
    if selected_date:
        select_year = datetime.strptime(selected_date, "%Y-%m").year
        select_month = datetime.strptime(selected_date, "%Y-%m").month
        session["workday_data"] = selected_date
        workday_date = session["workday_data"]
    else:
        select_year = datetime.today().year
        select_month = datetime.today().month
        workday_date = datetime.today().strftime("%Y-%m")

    return select_year, select_month, workday_date
