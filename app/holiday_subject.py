from __future__ import annotations
from datetime import datetime
from typing import List, Tuple
from abc import ABC, abstractmethod

from app import db
from app.models import User
from app.holiday_acquisition import HolidayAcquire

from app.holiday_observer import Observer


class Subject(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        pass

    @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        pass

    def acquire_holidays(self):
        raise NotImplementedError

    def execute(self) -> None:
        raise NotImplementedError


class SubjectImpl(Subject):
    """
    The Subject owns some important state and notifies observers when the state
    changes.
    """

    _state: int = None
    """
    For the sake of simplicity, the Subject's state, essential to all
    subscribers, is stored in this variable.
    """

    _observers: List[Observer] = []
    """
    List of subscribers. In real life, the list of subscribers can be stored
    more comprehensively (categorized by event type, etc.).
    """

    def attach(self, observer: Observer) -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    """
    The subscription management methods.
    """

    def notify(self) -> None:
        """
        Trigger an update in each subscriber.
        """

        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    def notice_month(self) -> int:
        now = datetime.now()
        self._state = 10 if (now.month == 10 and now.day == 1) else self._state
        self._state = 4 if (now.month == 4 and now.day == 1) else self._state
        return 4

    # def output_holiday_count(self, work_type: AcquisitionType, subscript: int) -> int:
    #     if subscript <= len(work_type.under5y) - 1:
    #         return work_type.under5y[subscript]
    #     else:
    #         return work_type.onward

    def get_concerned_staff(self) -> List[int]:
        concerned_id_list = []
        staff_id_list: List = (
            db.session.query(User.STAFFID).filter(User.INDAY != None).all()
        )
        for staff_id in staff_id_list:
            # STAFFIDを付ける、otherwise -> staff_id[0]
            holiday_acquire_obj = HolidayAcquire(staff_id.STAFFID)
            base_day = holiday_acquire_obj.convert_base_day()
            if base_day.month == self.notice_month():
                concerned_id_list.append(staff_id.STAFFID)

        return concerned_id_list

        # print("Notify!---処理が入ります。---")
        # return True

    def acquire_holidays(self, concerned_id: int) -> Tuple[int, float]:
        holiday_acquire_obj = HolidayAcquire(concerned_id)
        # 繰り越し日数
        carry_times: float = holiday_acquire_obj.print_remains()
        # 取得日数
        dict_value = holiday_acquire_obj.plus_next_holidays().values()
        # dict_valuesのリスト化
        acquisition_days: int = list(dict_value)[-1]
        # もしくは
        # base_day = holiday_acquire_obj.convert_base_day()
        # length: int = len(holiday_acquire_obj.get_acquisition_list(base_day))
        # 取得日数
        # acquisition_days = self.output_holiday_count(work_type, length)

        return (
            concerned_id,
            carry_times + acquisition_days * holiday_acquire_obj.job_time,
        )

        # return super().acquire_holidays()

    def execute(self) -> None:
        self.notify()
        # return super().execute()
