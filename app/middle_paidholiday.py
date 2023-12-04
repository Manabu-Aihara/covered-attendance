from datetime import date
from typing import Tuple, List
from dataclasses import dataclass
from abc import ABCMeta, abstractmethod

from app.content_paidholiday import HolidayAcquire, AcquisitionType
from app.content_paidholiday import HolidayCalcurate
from app.models_aprv import NotificationList, PaidHolidayLog


@dataclass
class PaidHolidayMiddleware:
    # スタッフID
    id: int

    def __post_init__(self):
        target_user = PaidHolidayLog.query.filter(
            self.id == PaidHolidayLog.STAFFID
        ).first()
        self.work_time: float = target_user.WORK_TIME

    # おそらく、暫定的なメソッド
    def output_acquisitions(self) -> Tuple[List[date], List[date]]:
        acquisition_holiday_obj = HolidayAcquire(self.id)
        start_list, end_list = acquisition_holiday_obj.print_holidays_data(
            AcquisitionType.A
        )
        return start_list, end_list

    # おそらく、暫定的なメソッド
    def output_remain_days(self, acquisition_type: AcquisitionType):
        # 暫定的に8時間勤務の年休付与タイプAの有効年休日数
        holiday_calc_obj = HolidayCalcurate(self.work_time, acquisition_type)
        enable_holidays = holiday_calc_obj.convert_tuple(
            holiday_calc_obj.get_sum_holiday(self.id)
        )
        return enable_holidays

    def make_paidholiday_log_data(
        self, notification_id: int, acquisition_type: AcquisitionType
    ) -> float:
        last_remain_days: float = (
            PaidHolidayLog.query.with_entities(PaidHolidayLog.REMAIN_DAYS)
            .filter(self.id == PaidHolidayLog.STAFFID)
            .order_by(PaidHolidayLog.REMAIN_DAYS)
            .first()
        )
        holiday_calc_obj = HolidayCalcurate(self.work_time, acquisition_type)
        new_remain = last_remain_days[0] - holiday_calc_obj.get_notification_rests(
            notification_id
        )
        return new_remain


# irregular
# class Observer(metaclass=ABCMeta):
#     @abstractmethod
#     def update(self, subject: Subject) -> None:
#         raise NotImplementedError


# class Subject(metaclass=ABCMeta):
#     def __init__(self) -> None:
#         self.__observers: list[Observer] = []

#     def add_observer(self, observer: Observer) -> None:
#         self.__observers.append(observer)

#     def delete_observer(self, observer: Observer) -> None:
#         self.__observers.remove(observer)

#     def notify_observer(self) -> None:
#         for o in self.__observers:
#             o.update(self)

#     @abstractmethod
#     def get_number(self) -> int:
#         raise NotImplementedError

#     @abstractmethod
#     def execute(self) -> None:
#         raise NotImplementedError
