from datetime import datetime
import calendar
import jpholiday
from typing import List
from dataclasses import dataclass


@dataclass
class NewCalendar:
    year: int
    month: int
    firstweekday: int = 6

    def get_itermonthdays(self) -> List[tuple]:
        calendar_obj = calendar.Calendar()
        twin_cals = calendar_obj.itermonthdays4(self.year, self.month)
        day_and_weeknum = []
        for twin_cal in twin_cals:
            if twin_cal[0] == 0:
                continue
            day_and_weeknum.append(twin_cal)
        return day_and_weeknum

    def __get_jp_holidays_num(self) -> List[int]:
        holiday_stock = []
        holidays = jpholiday.month_holidays(self.year, self.month)
        for holiday in holidays:
            holiday_stock.append(int(datetime.strftime(holiday[0], "%d")))
        return holiday_stock

    def get_weekday(self):
        # 土日を抜く
        weekdays: List[tuple] = list(
            filter(lambda d: d[1] != 5 and d[1] != 6, self.get_itermonthdays())
        )
        # 祝日を抜く
        weekdays: List[tuple] = list(
            filter(lambda d: d[0] not in self.__get_jp_holidays_num(), weekdays)
        )
        return weekdays

    def get_nth_dow(self, day: int) -> int:
        first_dow = calendar.monthrange(self.year, self.month)[0]
        offset = (first_dow - self.firstweekday) % 7
        return (day + offset - 1) // 7 + 1
