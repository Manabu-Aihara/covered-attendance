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


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_observer(app_context):
    subject = SubjectImpl()
    # observer = ObserverRegist()
    observer = ObserverCheck()

    subject.attach(observer)

    print(datetime.now())
    print(subject.execute())


@pytest.fixture
# @pytest.mark.freeze_time(datetime(2024, 3, 31))
def concerned_id_list(app_context, subject, mocker):
    mocker.patch.object(subject, "notice_month", return_value=datetime.now().month)
    print(datetime.now())
    return subject.get_concerned_staff()


# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_refer_acquire_type(app_context, subject, concerned_id_list, mocker):
    mocker.patch.object(HolidayAcquire, "count_workday", side_effect=[200, 65, 30])
    for concerned_id in concerned_id_list:
        print(f"{concerned_id}: {subject.refer_acquire_type(concerned_id)}")
