import pytest
from datetime import datetime
from typing import List

# from sqlalchemy import notin_

from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheck
from app.holiday_acquisition import AcquisitionType, HolidayAcquire
from app.models import User


@pytest.mark.skip
def test_print_db(app_context):
    acquisition_type_list: List[int, datetime] = (
        User.query.with_entities(User.STAFFID)
        # .join(RecordPaidHoliday, User.STAFFID == RecordPaidHoliday.STAFFID)
        # .filter(User.INDAY.is_not(None))でも大丈夫なようだ
        .filter(User.INDAY != None).all()
    )
    print(acquisition_type_list)


@pytest.fixture(scope="session")
def subject():
    subject = SubjectImpl()
    return subject


@pytest.mark.skip
def test_output_holiday_count(subject):
    # @param AcquisitionType
    # @return int
    count = subject.output_holiday_count(AcquisitionType.B, 5)
    print(count)


attendance_list_A = [19, 20, 17, 22, 17, 18, 19, 20, 17, 22, 17, 18]
attendance_list_B = [17, 15, 17]  # 新人さん、後で×4


@pytest.fixture
def get_concerned_id(app_context, subject, mocker):
    mocker.patch.object(subject, "notice_month", return_value=3)
    concerned_members = subject.get_concerned_staff()
    return concerned_members


# @pytest.mark.skip
def test_workday_count(app_context, subject, get_concerned_id, mocker):
    mocker.patch.object(
        HolidayAcquire, "count_workday", return_value=sum(attendance_list_A)
    )
    mocker.patch.object(
        HolidayAcquire,
        "count_workday_half_year",
        return_value=sum(attendance_list_B) * 4,
    )
    for id in get_concerned_id:
        print(subject.refer_acquire_type(id))


def func_now():
    return datetime.now()


@pytest.fixture(scope="session")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def fake_date():
    # assert func_now() == datetime(2024, 3, 31)
    # return func_now()
    # assert subject.notice_month() == 3
    print("前処理： function")
    yield func_now()
    print("後処理： function")


# @pytest.mark.skip
# @pytest.mark.usefixtures("fake_date")
# class ObserverTest:
#     def suite_test():
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_observer(app_context):
    subject = SubjectImpl()
    # observer = ObserverRegist()
    observer = ObserverCheck()

    subject.attach(observer)
    # print(subject.get_concerned_staff())
    # print(subject.acquire_holidays(20))
    print(datetime.now())
    print(subject.execute())
