from typing import Tuple, Callable
from datetime import date, datetime
from dataclasses import dataclass

from app.holiday_acquisition import HolidayAcquire, AcquisitionType
from app.models_aprv import NotificationList


@dataclass
class HolidayCalcurate:
    # 勤務時間
    job_time: int
    # 勤務形態 Acqisition.Aといった形式で指定
    work_type: AcquisitionType

    """
    勤務時間に応じた、申請時間を計算
    @Param
        notification_id: int
    @Return
        Tuple<申請日数: int | 申請時間: int>
    """

    def get_notification_rests(self, *notification_id: int) -> int:
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

        # .dayでintに変換
        day_side: int = (end_day.day - start_day.day) * self.job_time
        if start_time is not None and end_time is not None:
            comb_start: datetime = datetime.combine(start_day, start_time)
            comb_end: datetime = datetime.combine(end_day, end_time)
            # .hourでintに変換
            time_side = comb_end.hour - comb_start.hour
            return day_side + time_side
        else:
            return day_side

    """
    @Param
        staff_id: int
        carry_days: date
        # notification_id: int
    @Return
        Tuple<残り日数: int | 残り時間: int>
        """

    def get_sum_holiday(self, staff_id: int, carry_days: date = 0) -> int:
        acquisition_holiday_obj = HolidayAcquire(staff_id)
        holiday_dict = acquisition_holiday_obj.plus_next_holidays(self.work_type)
        holiday_list = []
        for holiday in holiday_dict.values():
            holiday_list.append(holiday)

        # 2年遡っての日数（2年消滅）＋繰り越し
        default_sum_holiday: int = (
            sum(holiday_list[-3:-1]) + int(carry_days)
            if len(holiday_list) >= 3
            else sum(holiday_list[:-1])
        )

        # 残り総合計時間
        sum_times: int = default_sum_holiday * self.job_time

        return sum_times

    def convert_tuple(self, func: Callable[..., int]) -> Tuple[int, int]:
        # func()はダメ
        return func // self.job_time, func % self.job_time

    # def get_remains(self, staff_id: int, notification_id: int) -> int:
    #     self.get_sum_holiday(staff_id) - self.get_notification_rests(notification_id)
