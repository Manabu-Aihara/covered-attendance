import pytest
from unittest.mock import PropertyMock
from datetime import datetime
from typing import List

from app.models import User
from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry
from app.holiday_acquisition import AcquisitionType, HolidayAcquire


# != Noneのやつ
@pytest.mark.skip
def test_print_db(app_context):
    acquisition_type_list: List[int, datetime] = (
        User.query.with_entities(User.STAFFID)
        # .join(RecordPaidHoliday, User.STAFFID == RecordPaidHoliday.STAFFID)
        # .filter(User.INDAY.is_not(None))でも大丈夫なようだ
        .filter(User.INDAY != None).all()
    )
    print(acquisition_type_list)


@pytest.fixture(scope="module")
@pytest.mark.freeze_time(datetime(2024, 3, 31, 7, 0, 0))
def subject():
    subject = SubjectImpl()
    return subject


@pytest.mark.skip
def test_output_holiday_count():
    # @param AcquisitionType
    # @return int
    count = subject.output_holiday_count(AcquisitionType.B, 5)
    print(count)


# ほぼ本番のやつ＊使用注意
@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_observer(app_context):
    subject = SubjectImpl()
    observer_regist = ObserverRegist()
    # observer_type = ObserverCheckType()
    # observer_carry = ObserverCarry()

    subject.attach(observer_regist)
    # subject.attach(observer_carry)

    print(datetime.now())
    print(subject.execute())


"""
    ここから、有用なテスト
    """


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_refer_acquire_type(app_context, subject, mocker):
    mocker.patch.object(subject, "notice_month", return_value=datetime.now().month)
    # print(datetime.now())
    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", return_value=200
    )
    workday_half_mock = mocker.patch.object(
        HolidayAcquire, "count_workday_half_year", side_effect=[230, 160]
    )

    print(subject.refer_acquire_type(31))
    print(subject.refer_acquire_type(40))
    print(subject.refer_acquire_type(201))

    assert workday_mock.call_count == 1
    assert workday_half_mock.call_count == 2


# Failed: DID NOT RAISE <class 'TypeError'>
# calcurate_carry_days()内のtry-exceptが、発生した例外をキャッチしていたから？
@pytest.mark.skip
def test_raise_carry_times(app_context, subject):
    with pytest.raises(TypeError) as exce_info:
        subject.calcurate_carry_times(31)
    print(exce_info.value)


@pytest.mark.skip
def test_raise_refer_holiday_type(app_context, subject):
    with pytest.raises(KeyError) as exce_info:
        subject.refer_acquire_type(40)
    print(exce_info.value)


# Failed: DID NOT RAISE <class 'KeyError'>
# 上同様try-exceptで、発生した例外をキャッチ済み
@pytest.mark.skip
def test_raise_acquire_holidays(app_context, subject):
    with pytest.raises(TypeError) as exec_info:
        subject.acquire_holidays(201)
    print(exec_info.value)


@pytest.mark.skip
def test_base_time_for_paid(app_context, subject):
    holiday_base = subject.get_holiday_base_time(165)
    assert holiday_base == 8.0


@pytest.mark.skip
# @pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_carry_times(app_context, subject):
    carry_times = subject.calcurate_carry_times(201)
    assert carry_times == 87.0


# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 4, 1, 7, 0, 0))
def test_acquire_holidays(app_context, subject):
    expection_holiday = subject.acquire_holidays(31)
    print(f"時間: {expection_holiday}")


@pytest.mark.skip
def test_divide_acquire_type(app_context, subject):
    expected_char = subject.divide_acquire_type(124)
    assert expected_char == "C"


@pytest.mark.skip
def test_calcurate_carry_days(app_context, subject, mocker):
    # 8時間労働と7時間労働のあり得る繰り越し時間
    remains_mock = mocker.patch.object(
        HolidayAcquire, "print_remains", side_effect=[80, 38.5]
    )
    sum_notify_mock = mocker.patch.object(
        HolidayAcquire, "sum_notify_times", side_effect=[13, 6]
    )

    print(subject.calcurate_carry_days(20))
    print(subject.calcurate_carry_days(30))

    print(sum_notify_mock.call_args_list)
    assert remains_mock.call_count == 2


"""
    ここまで
    """


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 4, 1, 7, 0, 0))
def test_get_concerned_staff(app_context, subject):
    sakura_member_list = subject.get_concerned_staff()
    print(sakura_member_list)
    print(len(sakura_member_list))


@pytest.mark.skip
def test_data_time():
    now = datetime.now()
    str_time = datetime(now.year, 4, 4, 12, 0, 0).strftime("%Y/%m/%d %H:%M:%S")
    print(str_time)


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 4, 1, 7, 0, 0))
def test_import_subject(subject):
    print(datetime.now())
    assert subject.notice_month() is not None


# コンストラクタモックは無理、引数あるから
# 使いどころあるのか、引き続き検討か


# def test_constructor(app_context, mocker):
#     # ha_mock = mocker.MagicMock()
#     # ha_mock.configure_mock(id=201)
#     ha_mock = mocker.patch("app.holiday_acquisition.HolidayAcquire", autospec=True)
#     property_mock = PropertyMock(return_value=201)
#     type(ha_mock).id = property_mock
#     ha_mock_201 = HolidayAcquire(201)
#     assert ha_mock == ha_mock_201
