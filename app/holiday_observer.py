# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
from typing import TYPE_CHECKING

from app import db
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog
from app.holiday_logging import get_logger

# 循環参照回避
if TYPE_CHECKING:
    from app.holiday_subject import Subject

# class PaidLogParse:
#     @classmethod
#     def insert_data(cls):
#         holiday_log_data = PaidHolidayLog(
#             concerned_id,
#             0,
#             None,
#             None,
#             carry_times / holiday_acquire_obj.job_time,
#             "前回からの繰り越し",
#         )
#         db.session.add(holiday_log_data)


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
            now = datetime.datetime.now()
            for concerned_id in subject.get_concerned_staff():
                print(subject.acquire_holidays(concerned_id))
                result_tuple: tuple = subject.acquire_holidays(concerned_id)
                print(result_tuple)
                # add_holidays = PaidHolidayLog(
                #     # スタッフID
                #     result_tuple[0],
                #     # 残り日数（繰り越し付き）
                #     result_tuple[1],
                #     None,
                #     None,
                #     0,
                #     f"{now.strftime('%Y/%m/%d')}付与",
                # )
                # db.session.add(add_holidays)

            # db.session.commit()


class ObserverCarry(Observer):
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
                    holiday_log_data = PaidHolidayLog(
                        concerned_id,
                        0,
                        None,
                        None,
                        carry_days,
                        "前回からの繰り越し",
                    )
                    db.session.add(holiday_log_data)
                    db.session.flush()
                    # self.trigger_fail(concerned_id)
                except TypeError as e:
                    print(f"{concerned_id}: {e}")
                    logger = get_logger(__name__, "ERROR")
                    logger.error(f"ID{concerned_id}: {e}")
                    db.session.rollback()
                else:
                    logger = get_logger(__name__, "INFO")
                    logger.info(f"ID{concerned_id}: {carry_days}日繰り越しました。")

            db.session.commit()


class ObserverCheckType(Observer):
    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---")
            for concerned_id in subject.get_concerned_staff():
                try:
                    before_type, after_type = subject.refer_acquire_type(concerned_id)
                    # print(paid_type)
                    if (before_type is None) or (before_type != after_type):
                        r_holiday_obj = RecordPaidHoliday(concerned_id)
                        r_holiday_obj.ACQUISITION_TYPE = after_type
                        db.session.merge(r_holiday_obj)
                        db.session.flush()
                except ValueError as e:
                    print(f"ID{concerned_id}: {e}")
                    logger = get_logger(__name__, "ERROR")
                    logger.error(f"ID{concerned_id}: {e}")
                    db.session.rollback()
                # これが全部反映しないと、commitしないタイプ
                else:
                    logger = get_logger(__name__, "INFO")
                    logger.info(f"ID{concerned_id}の年休付与タイプは「{after_type}」です。")

            db.session.commit()
