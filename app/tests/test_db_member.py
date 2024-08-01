import pytest

from app import db
from app.models import User, Busho, Post, Shinsei
from app.forms import AddDataUserForm
from app.routes_admin import get_user_role_list, get_user_role


@pytest.mark.skip
def test_get_role_list(app_context):
    test_role_list = get_user_role_list()
    assert len(test_role_list) == 8


@pytest.mark.skip
def test_get_user_role(app_context):
    test_result = get_user_role(Busho.NAME, Busho.CODE, 1)
    assert test_result == "本社"


@pytest.mark.skip
def test_add_user_form(app_context):
    for attr in AddDataUserForm.__dict__:
        print(attr)
    # print(getattr(AddDataUserForm, "department"))


def test_show_attendance(app_context):
    attendance_list = db.session.query(Shinsei).filter(Shinsei.STAFFID == 201).all()
    for attendance in attendance_list:
        print(attendance)
