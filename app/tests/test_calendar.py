import pytest
import datetime
from typing import Tuple

from app import db
from app.holiday_acquisition import HolidayAcquire, AcquisitionType
from app.content_paidholiday import HolidayCalcurate
from app.new_calendar import NewCalendar
from app.models_aprv import PaidHolidayModel


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(20)
    return acquisition_object


def test_convert_base_day(get_official_user):
    conv_date = get_official_user.convert_base_day()
    # print(conv_date)
    assert conv_date.month == 10


@pytest.mark.skip
def test_calcurate_days(get_official_user):
    final_data_list = get_official_user.print_date_type_list()
    print(final_data_list)


@pytest.mark.skip
def test_plus_2years_over_holidays(get_official_user):
    test_result_dict = get_official_user.plus_next_holidays(AcquisitionType.A)
    # print(AcquisitionType.A.__dict__["onward"])
    # print(AcquisitionType.A.under5y)
    print(test_result_dict)
    assert AcquisitionType.A.onward == 20


# @pytest.mark.skip
def test_print_holiday_data(get_official_user):
    print_result = get_official_user.print_holidays_data(AcquisitionType.A)
    print(print_result)


@pytest.mark.skip
def test_insert_ph_db(get_official_user):
    start_list, end_list, acquisition_list = get_official_user.print_holidays_data(
        AcquisitionType.A.under5y, AcquisitionType.A.onward
    )
    for start_day, end_day, acquisition in zip(start_list, end_list, acquisition_list):
        paid_holiday_obj = PaidHolidayModel(20)
        paid_holiday_obj.STAFFID = 20
        paid_holiday_obj.STARTDAY = start_day
        paid_holiday_obj.ENDDAY = end_day
        paid_holiday_obj.paid_holiday = acquisition
        print(paid_holiday_obj)
        # db.session.add(paid_holiday_obj)

    # db.session.commit()


# def test_get_remains(app_context):
#     hc_object = HolidayCalcurate(8, AcquisitionType.A)
#     result_tuple = hc_object.get_remains(20, 3)
#     print(result_tuple)


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
