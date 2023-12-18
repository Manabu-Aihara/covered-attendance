# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app import db
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog

# 循環参照回避
if TYPE_CHECKING:
    from app.holiday_subject import Subject


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        raise NotImplementedError


class ObserverRegist(Observer):
    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 4 or (
            notification_state := subject.notice_month()
        ) == 10:
            print(f"Notify!---{notification_state}月年休付与の処理が入ります。---")
            for concerned_id in subject.get_concerned_staff():
                print(subject.acquire_holidays(concerned_id))
            #     result_tuple: tuple = subject.acquire_holidays(concerned_id)
            #     add_holidays = PaidHolidayLog(result_tuple[0], result_tuple[1])
            #     db.session.add(add_holidays)

            # db.session.commit()


class ObserverCheck(Observer):
    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---")
            for concerned_id in subject.get_concerned_staff():
                print(subject.change_acquire_type())
                # paid_type = subject.change_acquire_type(concerned_id)
                # if char != enable_obj.acquisition_key:
                #     r_holiday_obj = RecordPaidHoliday(concerned_id)
                #     r_holiday_obj.ACQUISITION_TYPE = paid_type
                #     db.session.merge(r_holiday_obj)

            #     db.session.commit()
