import pytest
import math
from datetime import date, datetime, timedelta

from sqlalchemy import or_, and_
from sqlalchemy.sql import func

from app import db
from app.models import (
    User,
    Busho,
    KinmuTaisei,
    Shinsei,
    D_JOB_HISTORY,
    D_HOLIDAY_HISTORY,
)
from app.forms import AddDataUserForm
from app.jimu_oncall_count import get_more_condition_users
from app.attendance_query_class import AttendanceQuery
from app.attendance_util import get_user_role, check_table_member
from app.db_check_util import compare_db_item


@pytest.mark.skip
def test_get_user_role(app_context):
    user201 = db.session.get(User, 201)
    test_result = get_user_role(Busho.NAME, Busho.CODE, user201.DEPARTMENT_CODE)
    assert test_result == "本社"


@pytest.mark.skip
def test_add_user_form(app_context):
    for attr in AddDataUserForm.__dict__:
        print(attr)
    # print(getattr(AddDataUserForm, "department"))


@pytest.mark.skip
def test_raise_filter(app_context):
    # print(check_table_member(31, D_JOB_HISTORY))
    with pytest.raises(ValueError) as except_info:
        check_table_member(3, D_JOB_HISTORY)
    print(except_info.value)


@pytest.mark.skip
def test_show_attendance(app_context):
    attendance_list = db.session.query(Shinsei).filter(Shinsei.STAFFID == 201).all()
    for attendance in attendance_list:
        print(attendance)


@pytest.mark.skip
def test_join_data_count(app_context):
    join_info_objects = (
        db.session.query(User, D_JOB_HISTORY.JOBTYPE_CODE, D_JOB_HISTORY.CONTRACT_CODE)
        .outerjoin(D_JOB_HISTORY, D_JOB_HISTORY.STAFFID == User.STAFFID)
        .all()
    )
    # assert len(join_info_objects) == 8
    print(join_info_objects)


@pytest.mark.skip
def test_print_holiday(app_context):
    users = (
        db.session.query(D_JOB_HISTORY).filter(D_JOB_HISTORY.CONTRACT_CODE == 2).all()
    )
    user_time_dict = {}
    for user in users:
        user_time_dict = {
            "Staff": user.STAFFID,
            "Worktime": user.PART_WORKTIME,
        }
        print(f"{user_time_dict}")

    # holiday_his_lst = db.session.query(D_HOLIDAY_HISTORY).all()
    # holiday_time_dict = {}
    # for holi_his in holiday_his_lst:
    #     holiday_time_dict = {
    #         "Staff": holi_his.STAFFID,
    #         "Worktime": holi_his.HOLIDAY_TIME,
    #     }
    #     print(holiday_time_dict)


@pytest.mark.skip
def test_print_sub_holiday(app_context):
    part_users = db.session.query(User).filter(User.CONTRACT_CODE == 2).all()
    part_list = []
    for part_user in part_users:
        part_list.append(part_user.STAFFID)
    # for part_user in part_users:
    sub_q = (
        db.session.query(
            D_HOLIDAY_HISTORY.STAFFID,
            func.max(D_HOLIDAY_HISTORY.START_DAY).label("start_day_max"),
        )
        .filter(D_HOLIDAY_HISTORY.STAFFID.in_(part_list))
        .group_by(D_HOLIDAY_HISTORY.STAFFID)
        .subquery()
    )
    related_holiday_list = db.session.query(D_HOLIDAY_HISTORY).filter(
        and_(
            D_HOLIDAY_HISTORY.STAFFID == sub_q.c.STAFFID,
            D_HOLIDAY_HISTORY.START_DAY == sub_q.c.start_day_max,
        )
    )

    for related_holiday in related_holiday_list:
        print(f"{related_holiday.STAFFID}: {related_holiday.HOLIDAY_TIME}")


def test_count_three_if():
    cnt1: int = 0
    cnt2: int = 0
    for v in [("1", "1"), ("1", "2"), ("1", "0"), ("0", "2")]:
        cnt1 += 1 if v[0] == "1" else 0
        cnt2 += int(v[1]) if v[1] != "0" else 0

    assert cnt1 == 3
    assert cnt2 == 5


@pytest.fixture(name="cat_works")
def get_cat_attendance_member(app_context):
    filters = []
    from_day = datetime(year=2024, month=9, day=1)
    to_day = datetime(year=2024, month=9, day=30)
    filters.append(Shinsei.WORKDAY.between(from_day, to_day))
    filters.append(Shinsei.STAFFID == 84)
    # filters.append(User.CONTRACT_CODE == 2)
    # filters.append(Shinsei.MILEAGE != 0.0)
    concerned_attendances = (
        db.session.query(Shinsei)
        # .join(User, User.STAFFID == Shinsei.STAFFID)
        .filter(and_(*filters)).all()
    )
    # print(set(concerned_users))
    return concerned_attendances


@pytest.mark.skip
def test_print_work_time(cat_works):
    print(len(cat_works))
    time_list = []
    for cat_work in cat_works:
        start_date_type = datetime.strptime("8:00", "%H:%M")
        end_date_type = datetime.strptime(cat_work.ENDTIME, "%H:%M")
        diff_date = (
            end_date_type - start_date_type
            if cat_work.STARTTIME != "00:00"
            else timedelta(0)
        )
        print(f"Day: {cat_work.WORKDAY} Time: {diff_date}")
        time_list.append(diff_date.total_seconds())

    time_sum = math.fsum(time_list)
    print(f"Sum: {time_sum / 3600}")


@pytest.mark.skip
def test_compare_db_item(app_context):
    all_member = db.session.query(User).all()
    result_list = []
    for member in all_member:
        result = compare_db_item(member.STAFFID)
        result_list.append(result)

    print(result_list)


@pytest.fixture
def condition_users(app_context):
    sample_users = (
        db.session.query(User.STAFFID, User.INDAY, User.OUTDAY)
        # .filter(User.TEAM_CODE == 2)
        .all()
    )
    # print(sample_users)
    return sample_users


@pytest.mark.skip
def test_get_more_condition_users(condition_users):
    # assert isinstance(condition_users, list)
    test_users = get_more_condition_users(condition_users, "OUTDAY")
    print(test_users)


@pytest.mark.skip
def test_raise_more_condition_users(condition_users):
    with pytest.raises(TypeError) as except_info:
        get_more_condition_users(condition_users, "INDAY", "OUTDAY")
    print(except_info.value)


@pytest.fixture(name="aq")
def get_attendance_query_obj(app_context):
    from_day = date(2024, 10, 1)
    to_day = date(2024, 10, 31)
    aq_obj20 = AttendanceQuery(3, from_day, to_day)
    aq_obj201 = AttendanceQuery(201, from_day, to_day)
    return aq_obj20, aq_obj201


@pytest.mark.skip
def test_get_attendance_query(aq):
    querys = aq[0].get_attendance_query()
    cnt: int = 0
    for test_result in querys:
        # print(f"{i}query: {test_result[0]}")
        # assert test_result is None
        # assert isinstance(test_result[0].STAFFID, int)
        cnt += 1
    # assert type(aq[0]) is type(aq[1])
    assert cnt == 2


@pytest.mark.skip
def test_get_filter_length(aq):
    test_filter = aq[1]._get_filter(0, 6)
    assert len(test_filter) == 6
    # assert test_filter is None


@pytest.mark.skip
def test_get_clerical_attendance(aq):
    clerical_attendance_list = aq[1].get_clerical_attendance()
    cnt: int = 0
    for test_c_attendace in clerical_attendance_list:
        cnt += 1

    assert cnt == 5
