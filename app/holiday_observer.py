# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog
from app.holiday_acquisition import HolidayAcquire
from app.holiday_logging import get_logger

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


class ObserverCheck(Observer):
    def update(self, subject: Subject) -> None:
        # notification_state: int = subject.notice_month()
        if (notification_state := subject.notice_month()) == 3 or (
            notification_state := subject.notice_month()
        ) == 9:
            print(f"Notify!---{notification_state + 1}月年休付与前のチェックが入ります。---")
            for concerned_id in subject.get_concerned_staff():
                try:
                    holiday_acquire_obj = HolidayAcquire(concerned_id)
                    carry_times = subject.calcurate_carry_days(concerned_id)
                    # print(f"{concerned_id}: {carry_times}")
                    holiday_log_data = PaidHolidayLog(
                        concerned_id,
                        0,
                        None,
                        None,
                        carry_times * holiday_acquire_obj.job_time,
                        "前回からの繰り越し",
                    )
                    db.session.add(holiday_log_data)
                    db.session.commit()
                    logger = get_logger(__name__, "INFO")
                    logger.info(f"ID{concerned_id}: {carry_times}時間繰り越しました。")
                except Exception as e:
                    print(e)
                    db.session.rollback()

                try:
                    paid_type = subject.refer_acquire_type(concerned_id)
                    # print(paid_type)
                    holiday_acquire_obj = HolidayAcquire(concerned_id)
                    if (holiday_acquire_obj.acquisition_key is None) or (
                        holiday_acquire_obj.acquisition_key != paid_type
                    ):
                        r_holiday_obj = RecordPaidHoliday(concerned_id)
                        r_holiday_obj.ACQUISITION_TYPE = paid_type
                        db.session.merge(r_holiday_obj)
                        db.session.commit()
                        logger = get_logger(__name__, "INFO")
                        logger.info(f"ID{concerned_id}の年休付与タイプは「{paid_type}」です。")
                except Exception as e:
                    print(e)
                    db.session.rollback()
