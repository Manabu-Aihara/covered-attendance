import pytest
from datetime import datetime
from typing import List
import inspect

from app.models import User
from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry
from app.holiday_acquisition import AcquisitionType, HolidayAcquire


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
def subject():
    subject = SubjectImpl()
    return subject


@pytest.mark.skip
def test_output_holiday_count():
    # @param AcquisitionType
    # @return int
    count = subject.output_holiday_count(AcquisitionType.B, 5)
    print(count)


# ほぼ本番のやつ
@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_observer(app_context):
    subject = SubjectImpl()
    # observer = ObserverRegist()
    observer_type = ObserverCheckType()
    observer_carry = ObserverCarry()

    subject.attach(observer_type)
    subject.attach(observer_carry)

    print(datetime.now())
    print(subject.execute())


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_refer_acquire_type(app_context, subject, mocker):
    mocker.patch.object(subject, "notice_month", return_value=datetime.now().month)
    print(datetime.now())
    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", return_value=200
    )
    workday_half_mock = mocker.patch.object(
        HolidayAcquire, "count_workday_half_year", side_effect=[230, 160]
    )

    print(subject.refer_acquire_type(31))
    print(subject.refer_acquire_type(201))
    print(subject.refer_acquire_type(40))

    assert workday_mock.call_count == 1
    assert workday_half_mock.call_count == 2


# Failed: DID NOT RAISE <class 'TypeError'>
# calcurate_carry_days()内のtry-exceptが、発生した例外をキャッチしていたから？
@pytest.mark.skip
def test_raise_carry_days(app_context, subject):
    with pytest.raises(TypeError) as exce_info:
        subject.calcurate_carry_days(31)
    print(exce_info.value)


@pytest.mark.skip
def test_calcurate_carry_days(app_context, subject, mocker):
    # 8時間労働と7時間労働のあり得る繰り越し時間
    remains_mock = mocker.patch.object(
        HolidayAcquire, "print_remains", side_effect=[80, 38.5]
    )
    sum_notify_mock = mocker.patch.object(
        HolidayAcquire, "sum_notify_times", side_effect=[13, 45, 6, 20]
    )

    print(subject.calcurate_carry_days(20))
    print(subject.calcurate_carry_days(30))

    print(sum_notify_mock.call_args_list)
    assert remains_mock.call_count == 2


# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_check_observer(app_context, subject, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    acquisition_type_mock = mocker.patch.object(
        subject,
        "refer_acquire_type",
        side_effect=[(None, "B"), (None, "C"), (None, "A")],
    )

    # Save original function
    # original_trigger_fail = observer.trigger_fail

    # def mock_for_fail(i):
    #     """Mock throwing an exception when i == 2."""
    #     print(f"mock_insert_id called with i={i}")
    #     if i == 31:
    #         raise Exception("failed")
    #     original_trigger_fail(i)

    # mocker.patch.object(observer, "trigger_fail", side_effect=mock_for_fail)
    observer.update(subject)

    assert acquisition_type_mock.call_count == 3

    # 現状、不発
    def db_commit_mock(subject):
        print("Dummy insert")
        return False

    update_mock = mocker.patch.object(observer, "update", side_effect=db_commit_mock)
    subject.notify()

    assert update_mock.called


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_carry_observer(app_context, subject, mocker):
    observer = ObserverCarry()
    subject.attach(observer)

    # carry_days_mock = mocker.patch.object(subject, "calcurate_carry_days")
    observer.update(subject)

    # assert carry_days_mock.call_count == 3


# コンストラクタモックは無理、引数あるから
# 使いどころあるのか、引き続き検討か

# def test_constructor(app_context, mocker):
#     ha_mock = mocker.MagicMock()
#     mocker.patch("app.holiday_acquisition.HolidayAcquire", return_value=ha_mock)
#     ha_mock_201 = HolidayAcquire(201)
#     assert ha_mock == ha_mock_201
