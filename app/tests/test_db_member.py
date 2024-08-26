import pytest
from datetime import date, datetime

from sqlalchemy import or_, and_

from app import db
from app.models import User, Busho, Post, Shinsei
from app.forms import AddDataUserForm
from app.jimu_oncall_count import get_more_condition_users
from app.routes_admin import get_user_role
from app.attendance_query_class import AttendanceQuery


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
def test_show_attendance(app_context):
    attendance_list = db.session.query(Shinsei).filter(Shinsei.STAFFID == 201).all()
    for attendance in attendance_list:
        print(attendance)


@pytest.fixture
def condition_users(app_context):
    sample_users = (
        db.session.query(User.STAFFID, User.INDAY, User.OUTDAY)
        .filter(User.TEAM_CODE == 2)
        .all()
    )
    # print(sample_users)
    return sample_users


# @pytest.mark.skip
def test_get_more_condition_users(condition_users):
    # assert isinstance(condition_users, list)
    test_users = get_more_condition_users(condition_users, "INDAY", "OUTDAY")
    print(test_users)


@pytest.mark.skip
def test_raise_more_condition_users(condition_users):
    with pytest.raises(TypeError) as except_info:
        get_more_condition_users(condition_users, "INDAY", "OUTDAY")
    print(except_info.value)


@pytest.fixture(name="aq")
def get_attendance_query_obj(app_context):
    from_day = date(2024, 8, 1)
    to_day = date(2024, 8, 31)
    aq_obj20 = AttendanceQuery(20, from_day, to_day)
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
    assert cnt == 5


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
