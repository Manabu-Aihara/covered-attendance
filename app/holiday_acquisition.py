import enum
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from typing import List, Tuple, Callable
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from app.models import User, RecordPaidHoliday
from app.models_aprv import NotificationList, PaidHolidayLog


# コンストラクタを作って、その引数に、各項目に与えた値の
# 1つめ、2つめ、3つめが何を意味しているか名前を与えて、
# インスタンス変数に格納して上げると、特にインスタンスを作らなくても、
# アクセス出来るようになります。
# https://note.com/yucco72/n/ne69ea7fb26e7
class AcquisitionType(enum.Enum):
    A = (list(range(10, 12)) + list(range(12, 20, 2)), 20)  # 以降20 年間勤務日数>=217
    B = ([7, 8, 9, 10, 12, 13], 15)  # 以降15 年間勤務日数range(169, 216)
    C = ([5, 6, 6, 8, 9, 10], 11)  # 以降11 年間勤務日数range(121, 168)
    D = ([3, 4, 4, 5, 6, 6], 7)  # 以降7 年間勤務日数range(73, 120)
    E = ([1, 2, 2, 2, 3, 3], 3)  # 以降3 年間勤務日数range(48, 72)

    def __init__(self, under5y: list, onward: int):
        super().__init__()
        self.under5y = under5y
        self.onward = onward

    # 例: AからAcquisition.Aを引き出す
    @classmethod
    def name(cls, name: str) -> str:
        return cls._member_map_[name]


@dataclass
class HolidayAcquire:
    # スタッフID
    id: int

    def __post_init__(self):
        target_user = User.query.filter(User.STAFFID == self.id).first()
        if target_user.INDAY is not None:
            self.in_day = target_user.INDAY
        else:
            raise TypeError("User.INDAYの値がありません。")

        # 勤務時間
        # job_time: float
        self.job_time: float = (
            RecordPaidHoliday.query.with_entities(RecordPaidHoliday.WORK_TIME)
            .filter(self.id == RecordPaidHoliday.STAFFID)
            .first()
        )[0]

        # 勤務形態['A', 'B', 'C', 'D', 'E']
        self.acquisition_key: str = (
            RecordPaidHoliday.query.with_entities(RecordPaidHoliday.ACQUISITION_TYPE)
            .filter(self.id == RecordPaidHoliday.STAFFID)
            .first()
        )[0]

    """
    acquire: 日数
    get: 日付
    """

    def convert_base_day(self) -> datetime:
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

    # 付与日のリストを返す
    def get_acquisition_list(self, base_day: datetime) -> List[date]:
        holidays_get_list = []
        holidays_get_list.append(base_day.date())
        self.base_day = base_day + relativedelta(months=12)
        while base_day < datetime.today():
            if datetime.today() + relativedelta(months=12) < self.base_day:
                break
            return holidays_get_list + self.get_acquisition_list(self.base_day)

        return holidays_get_list
        # 次回付与日
        # return holidays_get_list[-1].date()

    # ちゃんとした付与日のリストを返すdata型で
    # base_day = self.convert_base_day()
    # [self.in_day.date()] + self.get_acquisition_list(base_day)

    # 入職日支給日数
    def acquire_start_holidays(self) -> OrderedDict[date, int]:
        base_day = self.convert_base_day()
        day_list = [self.in_day.date()] + self.get_acquisition_list(base_day)
        # monthmod(date.today(), base_day)[0].months < 6:
        if monthmod(self.in_day, base_day)[0].months <= 2:
            acquisition_days = 2
        elif monthmod(self.in_day, base_day)[0].months <= 3:
            acquisition_days = 1
        elif monthmod(self.in_day, base_day)[0].months > 3:
            acquisition_days = 0

        first_data = [(day_list[0], acquisition_days)]
        return OrderedDict(first_data)

    def convert_tuple(self, func: Callable[..., float]) -> Tuple[int, float]:
        # func()はダメ
        return func // self.job_time, func % self.job_time

    """
    勤務時間に応じた、申請時間を計算
    @Param
        notification_id: int
    @Return
        申請時間: float
    """

    def get_notification_rests(self, notification_id: int) -> float:
        start_day, end_day, start_time, end_time = (
            NotificationList.query.with_entities(
                NotificationList.START_DAY,
                NotificationList.END_DAY,
                NotificationList.START_TIME,
                NotificationList.END_TIME,
            )
            .filter(NotificationList.id == notification_id)
            .first()
        )

        end_day = start_day if end_day is None else end_day
        # datetime.timeのためにdatetimeに変換
        comb_start: datetime = datetime.combine(start_day, start_time)
        comb_end: datetime = datetime.combine(end_day, end_time)
        # 月をまたぐかもしれないので、単純にdayだけで計算できない
        diff_day: timedelta = end_day - start_day
        # 力技でtimedeltaをintに
        day_side: float = diff_day.total_seconds() // (3600 * 24) + 1
        # こちらは.hourでintに変換
        hour_side = comb_end.hour - comb_start.hour
        # いずれ30minutesを0.5で表したい
        minute_side = comb_end.minute - comb_start.minute
        return day_side * (hour_side if hour_side != 0 else self.job_time) + minute_side

    def print_remains(self) -> float:
        last_remain: float = (
            PaidHolidayLog.query.with_entities(PaidHolidayLog.REMAIN_TIMES)
            .filter(self.id == PaidHolidayLog.STAFFID)
            .order_by(PaidHolidayLog.id.desc())
            .first()
        )
        return last_remain[0]
        # - self.get_notification_rests(notification_id)で引き算

    """
    入職日＋以降の年休付与日数
    @Param
        frame: AcquisitionType  勤務形態
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    def plus_next_holidays(self) -> OrderedDict[date, int]:
        base_day = self.convert_base_day()
        day_list = [self.in_day.date()] + self.get_acquisition_list(base_day)
        holiday_pair = self.acquire_start_holidays()

        for i, acquisition_day in enumerate(
            AcquisitionType.name(self.acquisition_key).under5y
        ):
            if i == len(day_list) - 1:
                break
            else:
                holiday_pair[day_list[i + 1]] = acquisition_day

        if len(day_list) > len(AcquisitionType.name(self.acquisition_key).under5y):
            for day in day_list[7:]:
                holiday_pair[day] = AcquisitionType.name(self.acquisition_key).onward

        return holiday_pair

    """
    @Param
        staff_id: int
        carry_days: date
    @Return
        残り時間: float
        """

    def get_sum_holiday(self) -> float:
        holiday_dict = self.plus_next_holidays()
        holiday_list = []
        # holiday_dict.valuesは取得付与日数リスト
        for holiday in holiday_dict.values():
            holiday_list.append(holiday)

        # 2年遡っての日数（2年消滅）
        default_sum_holiday: int = (
            sum(holiday_list[-3:-1])
            if len(holiday_list) >= 3
            else sum(holiday_list[:-1])
        )

        acquisition_obj = HolidayAcquire(self.id)
        # 残り総合計時間
        sum_times: float = default_sum_holiday * (acquisition_obj.job_time)
        return sum_times

    # 表示用:STARTDAY, ENDDAYのペア
    def print_acquisition_data(self) -> Tuple[list[date], list[date]]:
        # 取得日、日数のペア
        holiday_dict = self.plus_next_holidays()

        end_day_list = [
            end_day + relativedelta(years=1, days=-1) for end_day in holiday_dict.keys()
        ]
        end_day_list[0] = ""
        return (list(holiday_dict.keys()), end_day_list)
