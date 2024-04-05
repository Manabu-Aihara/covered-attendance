import pytest
from datetime import datetime

import app
from app import db
from app.models_aprv import PaidHolidayLog
from app.holiday_acquisition import HolidayAcquire, AcquisitionType

TARGET_ID = 31


@pytest.fixture
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(TARGET_ID)
    return acquisition_object


# 基準日
# @pytest.mark.skip
def test_convert_base_day(get_official_user):
    conv_date = HolidayAcquire(TARGET_ID).convert_base_day(get_official_user.in_day)
    assert conv_date.month == 4


@pytest.mark.skip
def test_acquire_inday_holiday(get_official_user):
    test_dict = get_official_user.acquire_inday_holidays()
    # print(list(test_dict.values()))
    assert list(test_dict.values())[0] == 1


# @pytest.mark.skip
def test_get_acquisition_key(get_official_user):
    # with pytest.raises(KeyError) as except_info:
    test_type = get_official_user.get_acquisition_key()
    print(f"付与タイプ: {test_type}")


@pytest.mark.skip
def test_insert_new_user(get_official_user):
    test_dict = get_official_user.acquire_inday_holidays()
    pay_log_obj = PaidHolidayLog(
        get_official_user.id,
        list(test_dict.values())[0] * get_official_user.holiday_base_time,
        None,
        None,
        0,
        "入職日付与",
    )
    db.session.add(pay_log_obj)
    db.session.commit()


# https://stackoverflow.com/questions/1958219/how-to-convert-sqlalchemy-row-object-to-a-python-dict
def test_row2dict():
    paylog_obj = PaidHolidayLog
    d = {}
    for column in paylog_obj.__table__.columns:
        d[column.name] = str(getattr(paylog_obj, column.name))

    print(d)


# 付与リスト
@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 4, 1))
def test_get_acquisition_list(get_official_user):
    base_day = HolidayAcquire(TARGET_ID).convert_base_day(get_official_user.in_day)
    test_all_list = [
        get_official_user.in_day.date()
    ] + get_official_user.get_acquisition_list(base_day)
    # test_list = get_official_user.get_acquisition_list(base_day)
    print(f"付与リスト: {test_all_list}")


@pytest.mark.skip
def test_print_acquisition_data(get_official_user):
    test_from_to_list = get_official_user.print_acquisition_data()
    print(f"付与リストペア: {test_from_to_list}")


# 日数表示
@pytest.mark.skip
def test_convert_tuple(get_official_user):
    result_tuple = get_official_user.convert_tuple(get_official_user.get_sum_holiday())
    print(result_tuple)


# 年休関係ない申請例外
# @pytest.mark.skip
# def test_raise_notification_rests(get_official_user):
#     with pytest.raises(TypeError) as except_info:
#         get_official_user.get_notification_rests(31)
#     print(except_info.value)


# 特定申請時間計算
@pytest.mark.skip
def test_get_notification_rests(get_official_user):
    result_times = get_official_user.get_notification_rests(7)
    print(result_times)


@pytest.mark.skip
def test_raise_print_remains(get_official_user):
    with pytest.raises(TypeError) as except_info:
        get_official_user.print_remains()
    print(except_info.value)


# クラスメソッド、Enum
@pytest.mark.skip
def test_print_class_method(get_official_user):
    # print(AcquisitionType.A.__dict__["onward"])
    # print(AcquisitionType.A.under5y)
    print(AcquisitionType.name("A"))
    print(AcquisitionType.name(get_official_user.acquisition_key[0]))


# ACQUISITION_TYPEない例外
@pytest.mark.skip
def test_raise_acquisition_type(get_official_user):
    with pytest.raises(KeyError) as except_info:
        get_official_user.plus_next_holidays()
    print(except_info.value)


# @pytest.mark.skip
# @pytest.mark.freeze_time(datetime(2024, 4, 1))
def test_plus_next_holidays(get_official_user):
    test_value = get_official_user.plus_next_holidays()
    print(f"日付＆日数: {test_value}")


@pytest.mark.skip
def test_plus_next_holidays_log(get_official_user, mocker):
    log_mock = mocker.patch.object(
        app.holiday_logging, "get_logger", side_effect=Exception
    )
    get_official_user.plus_next_holidays()
    assert log_mock.called


# DBからとりあえず申請合計時間（時間休のみ）カウントできるか
# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_sum_notify_times(get_official_user):
    time_rest_sum = get_official_user.sum_notify_times(True)
    print(time_rest_sum)


# DBからとりあえず出勤日数カウントできるか
@pytest.mark.skip
def test_count_workday(get_official_user):
    test_count = get_official_user.count_workday()
    print(f"出勤日数カウント: {test_count}")


@pytest.mark.skip
def test_count_workday_half(get_official_user):
    test_count = get_official_user.count_workday_half_year()
    print(f"出勤日数カウント: {test_count}")


@pytest.mark.skip
def test_diff_month(get_official_user):
    test_diff = get_official_user.get_diff_month()
    assert test_diff == 1
