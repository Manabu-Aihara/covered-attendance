from typing import Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.holiday_acquisition import HolidayAcquire, AcquisitionType
from app.models_aprv import NotificationList, PaidHolidayLog


@dataclass
class HolidayCalcurate:
    # スタッフID
    # id: int
    # 勤務形態 Acqisition.Aといった形式で指定
    # work_type: AcquisitionType

    # 勤務時間
    # job_time: float
    def __post_init__(self):
        self.job_time: float = (
            PaidHolidayLog.query.with_entities(PaidHolidayLog.WORK_TIME)
            # .filter(self.id == PaidHolidayLog.STAFFID)
            .order_by(PaidHolidayLog.WORK_TIME.desc()).first()
        )

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

    """
    @Param
        staff_id: int
        carry_days: date
    @Return
        残り時間: float
        """

    def get_sum_holiday(self, staff_id: int, work_type: AcquisitionType) -> float:
        acquisition_holiday_obj = HolidayAcquire(staff_id)
        holiday_dict = acquisition_holiday_obj.plus_next_holidays(work_type)
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

        # 残り総合計時間
        sum_times: float = default_sum_holiday * self.job_time
        return sum_times

    def convert_tuple(self, func: Callable[..., float]) -> Tuple[int, float]:
        # func()はダメ
        return func // self.job_time, func % self.job_time

    # def get_remains(self, staff_id: int, *notification_list: int) -> float:
    #     i: int = 0
