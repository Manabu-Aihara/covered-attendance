import pytest
from datetime import datetime
from typing import List

# from sqlalchemy import notin_

from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverImpl
from app.models import RecordPaidHoliday, User


# @pytest.mark.skip
def test_observer(app_context):
    subject = SubjectImpl()
    observer = ObserverImpl()

    subject.attach(observer)

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
