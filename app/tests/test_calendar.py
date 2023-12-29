import pytest
from datetime import datetime

from app import db
from app.holiday_acquisition import HolidayAcquire, AcquisitionType
from app.new_calendar import NewCalendar
from app.models_aprv import PaidHolidayLog


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(31)
    return acquisition_object


# @pytest.mark.skip
def test_convert_base_day(get_official_user):
    conv_date = get_official_user.convert_base_day()
    print(conv_date)
    assert conv_date.month == 4


# @pytest.mark.skip
def test_get_acquisition_list(get_official_user):
    base_day = get_official_user.convert_base_day()
    test_all_list = [
        get_official_user.in_day.date()
    ] + get_official_user.get_acquisition_list(base_day)
    print(test_all_list)


@pytest.mark.skip
def test_convert_tuple(get_official_user):
    result_tuple = get_official_user.convert_tuple(get_official_user.get_sum_holiday())
    print(result_tuple)


@pytest.mark.skip
def test_get_notification_rests_raise(get_official_user):
    with pytest.raises(TypeError) as except_info:
        get_official_user.get_notification_rests(31)
    print(except_info.value)


@pytest.mark.skip
def test_get_notification_rests(get_official_user):
    result_times = get_official_user.get_notification_rests(7)
    print(result_times)


@pytest.mark.skip
def test_print_class_method(get_official_user):
    # print(AcquisitionType.A.__dict__["onward"])
    # print(AcquisitionType.A.under5y)
    print(AcquisitionType.name("A"))
    print(AcquisitionType.name(get_official_user.acquisition_key[0]))


@pytest.mark.skip
def test_plus_next_holidays(get_official_user):
    test_value = get_official_user.plus_next_holidays()
    print(test_value)


@pytest.mark.skip
def test_insert_notification_row(get_official_user):
    remain = get_official_user.print_remains()
    # print(get_official_user.get_notification_rests(53))
    pay_log_obj = PaidHolidayLog(
        20, remain - get_official_user.get_notification_rests(53), 53
    )
    db.session.add(pay_log_obj)
    db.session.commit()


@pytest.mark.skip
def test_insert_new_user(get_official_user):
    test_sum_holiday = get_official_user.get_sum_holiday()
    pay_log_obj = PaidHolidayLog(
        get_official_user.id, test_sum_holiday, None, None, "新規作成"
    )
    db.session.add(pay_log_obj)
    db.session.commit()


@pytest.mark.skip
def test_sum_notify_times(get_official_user):
    test_result = get_official_user.sum_notify_times(True)
    assert test_result == 3.0


@pytest.mark.skip
def test_count_workday(get_official_user):
    test_count = get_official_user.count_workday()
    assert test_count == 2


@pytest.mark.skip
def test_print_remains(get_official_user, mocker):
    last_remain = get_official_user.print_remains()
    # 適当な申請日数合計を2つ
    mocker.patch.object(
        HolidayAcquire,
        "sum_notify_times",
        side_effect=[get_official_user.sum_notify_times() * 8, 50.0],
    )
    result = (
        last_remain
        - get_official_user.sum_notify_times()
        - get_official_user.sum_notify_times(True)
    )
    print(result)


@pytest.mark.skip
def test_count_workday_half_year(get_official_user, mocker):
    mocker.patch.object(HolidayAcquire, "count_workday", return_value=49)
    result_count = get_official_user.count_workday_half_year()
    print(result_count)


# attendance_list_A = [19, 20, 17, 22, 17, 18, 19, 20, 17, 22, 17, 18]
attendance_list_B = [17, 15, 17]  # 新人さん、後で×4
attendance_list_C = [12, 10, 12, 12, 10, 11]


# @pytest.mark.skip
def test_get_nth_dow(get_official_user):
    nth_week = get_official_user.get_nth_dow()
    assert nth_week == 1


def test_get_diff_month(get_official_user):
    test_diff = get_official_user.get_diff_month()
    assert test_diff == 2


# @pytest.mark.skip
def test_count_workday_half(get_official_user, mocker):
    mocker.patch.object(
        HolidayAcquire, "count_workday", return_value=sum(attendance_list_C[1:])
    )
    # mocker.patch.object(HolidayAcquire, "get_diff_month", return_value=5)
    test_workday = get_official_user.count_workday_half_year()
    print(test_workday)


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
