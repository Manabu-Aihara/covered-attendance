import pytest

from app.holiday_acquisition import HolidayAcquire, AcquisitionType


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(31)
    return acquisition_object


# 基準日
# @pytest.mark.skip
def test_convert_base_day(get_official_user):
    conv_date = get_official_user.convert_base_day()
    print(conv_date)
    assert conv_date.month == 4


# 付与リスト
# @pytest.mark.skip
def test_get_acquisition_list(get_official_user):
    base_day = get_official_user.convert_base_day()
    test_all_list = [
        get_official_user.in_day.date()
    ] + get_official_user.get_acquisition_list(base_day)
    print(test_all_list)


# 日数表示
@pytest.mark.skip
def test_convert_tuple(get_official_user):
    result_tuple = get_official_user.convert_tuple(get_official_user.get_sum_holiday())
    print(result_tuple)


# 年休関係ない申請例外
@pytest.mark.skip
def test_raise_notification_rests(get_official_user):
    with pytest.raises(TypeError) as except_info:
        get_official_user.get_notification_rests(31)
    print(except_info.value)


# 特定申請時間計算
@pytest.mark.skip
def test_get_notification_rests(get_official_user):
    result_times = get_official_user.get_notification_rests(7)
    print(result_times)


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
def test_plus_next_holidays(get_official_user):
    test_value = get_official_user.plus_next_holidays()
    print(f"NEXT: {test_value}")


# DBからとりあえず申請合計時間（時間休のみ）カウントできるか
@pytest.mark.skip
def test_sum_notify_times(get_official_user):
    test_result = get_official_user.sum_notify_times(True)
    assert test_result == 3.0


# DBからとりあえず出勤日数カウントできるか
@pytest.mark.skip
def test_count_workday(get_official_user):
    test_count = get_official_user.count_workday()
    assert test_count == 2
