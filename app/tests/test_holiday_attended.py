import pytest
from datetime import datetime
import re

import pandas as pd
from sqlalchemy import and_, or_

from app import db
from app.models import RecordPaidHoliday, Shinsei
from app.holiday_acquisition import HolidayAcquire
from app.holiday_detail import AttendaceNotice
from app.calc_work_classes_diff import convert_ym_date, extract_last_update

TARGET_ID = 176


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(TARGET_ID)
    return acquisition_object


@pytest.mark.skip
def test_make_filter(get_official_user):
    base_day = HolidayAcquire(TARGET_ID).convert_base_day(get_official_user.in_day)
    test_filters = []
    test_filters.append(Shinsei.STAFFID == TARGET_ID)
    test_filters.append(or_(Shinsei.NOTIFICATION != "", Shinsei.NOTIFICATION2 != ""))
    test_filters.append(
        Shinsei.WORKDAY >= get_official_user.get_acquisition_list(base_day)[-2]
    )
    test_id_attendance_all = (
        # filter内andは当てにならん
        db.session.query(Shinsei)
        .filter(and_(*test_filters))
        .all()
    )
    # print(len(test_id_attendance_all))
    for test_id_attendance in test_id_attendance_all:
        print(
            f"{test_id_attendance.WORKDAY}: {test_id_attendance.NOTIFICATION} \
                {test_id_attendance.NOTIFICATION2}"
        )
    print("End")


@pytest.mark.skip
def test_count_attend_notificatin(app_context):
    attenntion_nofice_obj = AttendaceNotice(TARGET_ID)
    rp_holiday = db.session.get(RecordPaidHoliday, TARGET_ID)
    count = attenntion_nofice_obj.count_attend_notification()
    # print(
    #     f"ID{TARGET_ID}: {rp_holiday.REMAIN_PAIDHOLIDAY} {rp_holiday.USED_PAIDHOLIDAY}"
    # )
    print(f"使った日数: {count}")


@pytest.mark.skip
def test_sum_attend_time_rest(app_context):
    attenntion_nofice_obj = AttendaceNotice(TARGET_ID)
    count = attenntion_nofice_obj.sum_attend_time_rest()
    # print(f"使った日数: {count}")
    assert count == 7


@pytest.mark.skip
def test_re_replace():
    s = "12:34:00"
    # date_t = datetime.strptime(s, "%h:%m:%s")

    re_result = re.sub(r"(\d{2}):(\d{2}):00", r"\1:\2", s)
    assert re_result == "12:34"
    assert isinstance(re_result, str)


def test_convert_ym_date():
    result_regex = convert_ym_date("2024-11")
    print(result_regex)
    print(type(result_regex))


def test_extract_last_attend():
    result = extract_last_update("2024-11")
    # print(result_sr.to_dict().values())
    # print(type(result_df.loc[:, "Date"]))
    print(result)
    print(type(result))

    # assert result_df.size == 3
