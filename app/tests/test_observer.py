import pytest
from datetime import datetime
from typing import List

# from sqlalchemy import notin_

from app.holiday_subject import SubjectImpl, WorkdayType
from app.holiday_observer import ObserverRegist
from app.holiday_acquisition import AcquisitionType
from app.models import User


@pytest.fixture
def subject():
    subject = SubjectImpl()
    return subject


@pytest.mark.skip
def test_observer(app_context):
    subject = SubjectImpl()
    observer = ObserverRegist()

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


def test_output_workday_type():
    for char in ["B", "C", "D", "E"]:
        if 250 in list(WorkdayType.name(char).value):
            break
        else:
            char = "A"

    print(char)
