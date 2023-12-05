from datetime import date, datetime, timedelta
from dataclasses import dataclass
from typing import List, Tuple, Callable
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from app.models import User, RecordPaidHoliday
from app.models_aprv import NotificationList, PaidHolidayLog


@dataclass
class HolidayAcquire:
    # スタッフID
    id: int

    def __post_init__(self):
        target_user = User.query.filter(User.STAFFID == self.id).first()
        self.in_day: datetime = target_user.INDAY

        # 勤務時間
        # job_time: float
        # def __post_init__(self):
        # self.job_time: float = (
        #     PaidHolidayLog.query.with_entities(PaidHolidayLog.WORK_TIME)
        #     .filter(self.id == PaidHolidayLog.STAFFID)
        #     .order_by(PaidHolidayLog.WORK_TIME.desc()).first()
        # )
        self.job_time: float = (
            RecordPaidHoliday.query.with_entities(
                RecordPaidHoliday.WORK_TIME, RecordPaidHoliday.ACQUISITION_TYPE
            )
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
