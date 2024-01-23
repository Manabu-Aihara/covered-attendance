# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
from typing import TYPE_CHECKING

from app import db
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog
from app.holiday_logging import HolidayLogger

# 循環参照回避
if TYPE_CHECKING:
    from app.holiday_subject import Subject


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        raise NotImplementedError


class ObserverRegist(Observer):
    def insert_data(self, i: int, calc_data: float) -> None:
        now = datetime.datetime.now()
        add_holidays = PaidHolidayLog(
            # スタッフID
            i,
            # 残り日数（繰り越し付き）
            calc_data,
            None,
            None,
            0,
            f"{now.strftime('%Y/%m/%d')}付与",
        )
        db.session.add(add_holidays)

    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 4 or (
            notification_state := subject.notice_month()
        ) == 10:
            print(f"Notify!---{notification_state}月年休付与の処理が入ります。---")
            for concerned_id in subject.get_concerned_staff():
                try:
                    result_times, day_acquired = subject.acquire_holidays(concerned_id)
                    print(result_times)
                    self.insert_data(concerned_id, result_times)
                except ValueError as e:
                    print(f"ID{concerned_id}: {e}")
                    logger = HolidayLogger.get_logger("ERROR")
                    logger.error(f"ID{concerned_id}: {e}")
                    db.session.rollback()
                else:
                    logger = HolidayLogger.get_logger("INFO")
                    logger.info(f"ID{concerned_id}: {day_acquired}日付与されました。")

            db.session.commit()


class ObserverCarry(Observer):
    def trigger_fail(self, i):
        """Dummy for trigger fail"""
        print(f"trigger_fail() i={i}")

    def insert_data(self, i: int, calc_data: float):
        holiday_log_data = PaidHolidayLog(
            i,
            0,
            None,
            None,
            calc_data,
            "前回からの繰り越し",
        )
        db.session.add(holiday_log_data)

    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---")
            for concerned_id in subject.get_concerned_staff():
                try:
                    carry_days = subject.calcurate_carry_days(concerned_id)
                    # print(f"{concerned_id}: {carry_times}")
                    self.insert_data(concerned_id, carry_days)
                    db.session.flush()
                    # self.trigger_fail(concerned_id)
                except TypeError as e:
                    print(f"{concerned_id}: {e}")
                    logger = HolidayLogger.get_logger("ERROR")
                    logger.error(f"ID{concerned_id}: {e}")
                    db.session.rollback()
                # これが全部反映しないと、commitしないタイプ
                else:
                    logger = HolidayLogger.get_logger("INFO")
                    logger.info(f"ID{concerned_id}: {carry_days}日繰り越しました。")

            db.session.commit()


class ObserverCheckType(Observer):
    def trigger_fail(self, i):
        """Dummy for trigger fail"""
        print(f"trigger_fail() i={i}")

    def merge_type(self, i: int, past: str, post: str):
        if (past is None) or (post != post):
            r_holiday_obj = RecordPaidHoliday(i)
            r_holiday_obj.ACQUISITION_TYPE = post

    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---")
            for concerned_id in subject.get_concerned_staff():
                try:
                    before_type, after_type = subject.refer_acquire_type(concerned_id)
                    # print(before_type, after_type)
                    self.merge_type(concerned_id, before_type, after_type)
                    db.session.flush()
                    # self.trigger_fail(concerned_id)
                    # db.session.commit()
                except ValueError as e:
                    # print(f"ID{concerned_id}: {e}")
                    logger = HolidayLogger.get_logger("ERROR")
                    logger.error(f"ID{concerned_id}: {e}")
                    db.session.rollback()
                else:
                    logger = HolidayLogger.get_logger("INFO")
                    logger.info(f"ID{concerned_id}の年休付与タイプは「{after_type}」です。")

            db.session.commit()
