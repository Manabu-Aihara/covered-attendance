import pytest
from typing import List

from app import db
from app.holiday_acquisition import HolidayAcquire
from app.new_calendar import NewCalendar
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(31)
    return acquisition_object


# 年休関連、必要情報
@pytest.mark.skip
def test_get_holiday_info(app_context):
    target_user_info = (
        db.session.query(RecordPaidHoliday.STAFFID, RecordPaidHoliday.WORK_TIME)
        .filter(
            HolidayAcquire(RecordPaidHoliday.STAFFID).convert_base_day().month == int(4)
        )
        .all()
    )
    print(target_user_info)


"""
    D_PAIDHOLIDAY_LOG、insert処理
    現状使えない…カラム増やしてるから
    """


@pytest.mark.skip
def test_insert_notification_row(get_official_user):
    remain = get_official_user.print_remains()
    # print(get_official_user.get_notification_rests(53))
    pay_log_obj = PaidHolidayLog(
        20, remain - get_official_user.get_notification_rests(53), 53
    )
    db.session.add(pay_log_obj)
    db.session.commit()


# attendance_list_A = [19, 20, 17, 22, 17, 18, 19, 20, 17, 22, 17, 18]
attendance_list_B = [17, 15, 17]  # 新人さん、後で×4
attendance_list_C = [12, 10, 12, 12, 10, 11]


# おニューカレンダーテスト
@pytest.fixture
def make_new_calendar():
    new_calendar = NewCalendar(2023, 12)
    return new_calendar


@pytest.mark.skip
def test_get_itermonthdays(make_new_calendar):
    result = make_new_calendar.get_itermonthdays()
    print(result)


@pytest.mark.skip
def test_get_month_holidays_num(make_new_calendar):
    print(make_new_calendar.__get_jp_holidays_num())


@pytest.mark.skip
def test_get_weekday(make_new_calendar):
    print(make_new_calendar.get_weekday())
