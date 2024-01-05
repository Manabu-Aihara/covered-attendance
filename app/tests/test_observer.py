import pytest
from datetime import datetime
from typing import List

from app.models import User
from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheck
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
    observer = ObserverCheck()

    subject.attach(observer)

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
        HolidayAcquire, "count_workday_half_year", side_effect=[160, 230]
    )
    print(type(workday_half_mock))

    subject.refer_acquire_type(201)
    subject.refer_acquire_type(31)
    subject.refer_acquire_type(40)

    assert workday_mock.call_count == 1
    assert workday_half_mock.call_count == 2


# コンストラクタモックは無理、引数あるから
# 使いどころあるのか、引き続き検討か

# def test_constructor(app_context, mocker):
#     ha_mock = mocker.MagicMock()
#     mocker.patch("app.holiday_acquisition.HolidayAcquire", return_value=ha_mock)
#     ha_mock_201 = HolidayAcquire(201)
#     assert ha_mock == ha_mock_201
