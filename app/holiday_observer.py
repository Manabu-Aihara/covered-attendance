# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

# 循環参照回避
if TYPE_CHECKING:
    from app.holiday_subject import Subject

from app.models import RecordPaidHoliday, User
from app.holiday_acquisition import HolidayAcquire


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        raise NotImplementedError


class ObserverImpl(Observer):
    def update(self, subject: Subject) -> None:
        flag = subject.notice_acquisition_day()
        # acquisition_type_list: List[int, str] = []
        if flag is True:
            acquisition_type_list: List[int, str] = (
                User.query.with_entities(
                    User.STAFFID, RecordPaidHoliday.ACQUISITION_TYPE
                )
                .join(RecordPaidHoliday, User.STAFFID == RecordPaidHoliday.STAFFID)
                .filter(User.INDAY != None)
                .all()
            )
            # print(f"In Observer{acquisition_type_list}")
            for acquisition_type in acquisition_type_list:
                holiday_acquire_obj = HolidayAcquire(acquisition_type[0])
                base_day = holiday_acquire_obj.convert_base_day()
                if base_day.month == 10:
                    dict_value = holiday_acquire_obj.plus_next_holidays().values()
                    # dict_valuesのリスト化
                    acquisition_days: int = list(dict_value)[-1]
                    print(acquisition_days)
                    # return acquisition_days
        else:
            pass

        # return super().update(subject)
