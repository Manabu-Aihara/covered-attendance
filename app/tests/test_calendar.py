import pytest

from app import db
from app.holiday_acquisition import HolidayAcquire, AcquisitionType
from app.new_calendar import NewCalendar
from app.models_aprv import PaidHolidayLog


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(20)
    return acquisition_object


@pytest.mark.skip
def test_convert_base_day(get_official_user):
    conv_date = get_official_user.convert_base_day()
    assert conv_date.month == 10


@pytest.mark.skip
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


# @pytest.mark.skip
def test_get_notification_rests_raise(get_official_user):
    with pytest.raises(TypeError) as except_info:
        get_official_user.get_notification_rests(31)
    print(except_info.value)


@pytest.mark.skip
def test_get_notification_rests(get_official_user):
    result_times = get_official_user.get_notification_rests(7)
    print(result_times)


# @pytest.mark.skip
# def test_insert_ph_db(get_official_user):
#     start_list, end_list, acquisition_list = get_official_user.print_holidays_data(
#         AcquisitionType.A.under5y, AcquisitionType.A.onward
#     )
#     for start_day, end_day, acquisition in zip(start_list, end_list, acquisition_list):
#         paid_holiday_obj = PaidHolidayModel(20)
#         paid_holiday_obj.STAFFID = 20
#         paid_holiday_obj.STARTDAY = start_day
#         paid_holiday_obj.ENDDAY = end_day
#         paid_holiday_obj.paid_holiday = acquisition
#         print(paid_holiday_obj)
#     db.session.add(paid_holiday_obj)

# db.session.commit()


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


# @pytest.mark.skip
def test_sum_notification(get_official_user):
    test_result = get_official_user.sum_notify_times()
    print(test_result)


@pytest.mark.skip
def test_print_remains(get_official_user):
    last_remain = get_official_user.print_remains()
    assert last_remain == 39


@pytest.mark.skip
def test_paid_log_db(get_official_user):
    remain = get_official_user.print_remains()
    # print(get_official_user.get_notification_rests(53))
    pay_log_obj = PaidHolidayLog(
        20, remain - get_official_user.get_notification_rests(53), 53
    )
    db.session.add(pay_log_obj)
    db.session.commit()


# おニューカレンダーテスト
@pytest.fixture
def make_new_calendar():
    new_calendar = NewCalendar(2023, 9)
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
