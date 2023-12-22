import pytest
import unittest
from datetime import datetime
from typing import List

# from sqlalchemy import notin_

from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheck
from app.holiday_acquisition import AcquisitionType, HolidayAcquire
from app.models import User


@pytest.fixture
def subject():
    subject = SubjectImpl()
    return subject


@pytest.mark.skip
def test_observer(app_context):
    subject = SubjectImpl()
    # observer = ObserverRegist()
    observer = ObserverCheck()

    subject.attach(observer)
    # print(subject.get_concerned_staff())
    # print(subject.acquire_holidays(20))

    print(subject.execute())


@pytest.mark.skip
def test_print_db(app_context):
    acquisition_type_list: List[int, datetime] = (
        User.query.with_entities(User.STAFFID)
        # .join(RecordPaidHoliday, User.STAFFID == RecordPaidHoliday.STAFFID)
        # .filter(User.INDAY.is_not(None))でも大丈夫なようだ
        .filter(User.INDAY != None).all()
    )
    print(acquisition_type_list)


@pytest.mark.skip
def test_output_holiday_count(subject):
    # @param AcquisitionType
    # @return int
    count = subject.output_holiday_count(AcquisitionType.B, 5)
    print(count)


@pytest.mark.skip
def test_refer_acquire_type(subject):
    result = subject.refer_acquire_type()
    assert result == "A"

    # class TestObserverClass(unittest.TestCase):
    #     def setUp(self):


attendance_list_A = [19, 20, 17, 22, 17, 18, 19, 20, 17, 22, 17, 18]
attendance_list_B = [17, 15, 17]


def test_notice_month(app_context, subject, mocker):
    mock = mocker.patch.object(datetime, "now", return_value=datetime(2024, 9, 30))
    print(mock.now())
    # assert subject.notice_month() == 9


def test_workday_count(app_context, subject, mocker):
    mocker.patch.object(
        HolidayAcquire, "count_workday", return_value=sum(attendance_list_A)
    )
    assert subject.refer_acquire_type(20) == "A"
