import pytest
from datetime import date

from app import db
from app.models import User, Busho, Post, Shinsei
from app.forms import AddDataUserForm
from app.routes_admin import get_user_role_list, get_user_role
from app.attendance_query_class import AttendanceQuery


@pytest.mark.skip
def test_get_role_list(app_context):
    test_role_list = get_user_role_list()
    assert len(test_role_list) == 8


@pytest.mark.skip
def test_get_user_role(app_context):
    test_result = get_user_role(Busho.NAME, Busho.CODE, 1)
    assert test_result == "本社"


@pytest.fixture(name="aq")
def get_attendance_query_obj(app_context):
    from_day = date(2024, 8, 1)
    to_day = date(2024, 8, 31)
    aq_obj = AttendanceQuery(20, from_day, to_day)
    return aq_obj


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


@pytest.mark.skip
def test_get_attendance_query(aq):
    querys = aq.get_attendance_query()
    for test_result in querys:
        print(test_result[0].WORKDAY)


def test_get_filter_length(aq):
    test_filter = aq._get_filter()
    assert len(test_filter) == 8
    # assert test_filter is None
