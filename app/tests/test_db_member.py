import pytest
from datetime import date

from app import db
from app.models import User, Busho, Post, Shinsei
from app.forms import AddDataUserForm
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


@pytest.fixture(name="aq")
def get_attendance_query_obj(app_context):
    from_day = date(2024, 8, 1)
    to_day = date(2024, 8, 31)
    aq_obj20 = AttendanceQuery(20, from_day, to_day)
    aq_obj201 = AttendanceQuery(201, from_day, to_day)
    return aq_obj20, aq_obj201


# @pytest.mark.skip
def test_get_attendance_query(aq):
    querys = aq[1].get_attendance_query()
    for i, test_result in enumerate(querys):
        print(f"{i}query: {test_result[0]}")
        # assert test_result is None
        assert isinstance(test_result[0].STAFFID, int)
    # assert type(aq[0]) is type(aq[1])


@pytest.mark.skip
def test_get_filter_length(aq):
    test_filter = aq._get_filter()
    assert len(test_filter) == 8
    # assert test_filter is None
