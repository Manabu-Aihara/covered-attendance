import enum
from datetime import date, datetime
from dataclasses import dataclass
from typing import List, Tuple
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from app.models import User


# コンストラクタを作って、その引数に、各項目に与えた値の
# 1つめ、2つめ、3つめが何を意味しているか名前を与えて、
# インスタンス変数に格納して上げると、特にインスタンスを作らなくても、
# アクセス出来るようになります。
# https://note.com/yucco72/n/ne69ea7fb26e7
class AcquisitionType(enum.Enum):
    A = (list(range(10, 12)) + list(range(12, 20, 2)), 20)  # 以降20
    B = ([7, 8, 9, 10, 12, 13], 15)  # 以降15
    C = ([5, 6, 6, 8, 9, 10], 11)  # 以降11
    D = ([3, 4, 4, 5, 6, 6], 7)  # 以降7
    E = ([1, 2, 2, 2, 3, 3], 3)  # 以降3

    def __init__(self, under5y: list, onward: int):
        super().__init__()
        self.under5y = under5y
        self.onward = onward


@dataclass
class HolidayAcquire:
    id: int

    def __post_init__(self):
        target_user = User.query.filter(User.STAFFID == self.id).first()
        self.in_day: date = target_user.INDAY

    """
    acquire: 日数
    get: 日付
    """

    def convert_base_day(self) -> date:
        # 基準月に変換
        #     入社日が4月〜9月
        #     10月1日に年休付与
        if self.in_day.month >= 4 and self.in_day.month < 10:
            change_day = self.in_day.replace(month=10, day=1)  # 基準月
            return change_day  # 初回付与日

        #     入社日が10月〜12月
        #     翌年4月1日に年休付与
        elif self.in_day.month >= 10 and self.in_day.month <= 12:
            change_day = self.in_day.replace(month=4, day=1)
            return change_day + relativedelta(months=12)

        #     入社日が1月〜3月
        #     4月1日に年休付与
        elif self.in_day.month < 4:
            change_day = self.in_day.replace(month=4, day=1)
            return change_day

    # 付与日のリストを返す（一回足りないか？）
    def __calcurate_days(self, base_day: date) -> List[datetime]:
        holidays_get_list = []
        self.base_day = base_day + relativedelta(months=12)
        while base_day < datetime.today():
            holidays_get_list.append(self.base_day)
            if datetime.today() < self.base_day:
                break
            return holidays_get_list + self.__calcurate_days(self.base_day)

        return holidays_get_list
        # 次回付与日
        # return holidays_get_list[-1].date()

    # ちゃんとした付与日のリストを返すdata型で
    def print_date_type_list(self) -> List[date]:
        base_day = self.convert_base_day()
        type_conv_list = [hl.date() for hl in self.__calcurate_days(base_day)]
        type_conv_list.insert(0, self.in_day.date())
        type_conv_list.insert(1, base_day.date())
        return type_conv_list

    # おそらくこれも次回付与日を求める
    # def get_next_holiday(self):
    #     base_day = self.convert_base_day()

    #     next_acquire_day = date(date.today().year, base_day.month, 1)
    #     return next_acquire_day

    # 入職日支給日数
    def acquire_start_holidays(self) -> OrderedDict[date, int]:
        base_day = self.convert_base_day()
        day_list = self.print_date_type_list()
        # monthmod(date.today(), base_day)[0].months < 6:
        if monthmod(self.in_day, base_day)[0].months <= 2:
            acquisition_days = 2
        elif monthmod(self.in_day, base_day)[0].months <= 3:
            acquisition_days = 1
        elif monthmod(self.in_day, base_day)[0].months > 3:
            acquisition_days = 0

        first_data = [(day_list[0], acquisition_days)]
        return OrderedDict(first_data)

    """
    入職日＋以降の年休付与日数
    @Param
        frame: AcquisitionType  勤務形態
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    # def plus_next_holidays(
    #     self, next_list: List[int], onward: int
    # ) -> OrderedDict[date, int]:
    def plus_next_holidays(self, frame: AcquisitionType) -> OrderedDict[date, int]:
        day_list = self.print_date_type_list()
        holiday_pair = self.acquire_start_holidays()

        for i, acquisition_day in enumerate(frame.under5y):
            if i == len(day_list):
                break
            else:
                holiday_pair[day_list[i + 1]] = acquisition_day

        if len(day_list) > len(frame.under5y):
            for day in day_list[7:]:
                holiday_pair[day] = frame.onward

        return holiday_pair

    # ENDDAYを含めた表示・DBinsert用
    def print_holidays_data(
        self, frame: AcquisitionType
    ) -> Tuple[list[date], list[date], list[int]]:
        # 取得日、日数のペア
        holiday_dict = self.plus_next_holidays(frame)

        end_day_list = [
            end_day + relativedelta(years=1, days=-1) for end_day in holiday_dict.keys()
        ]

        return (
            list(holiday_dict.keys()),
            end_day_list,
            list(holiday_dict.values()),
        )
