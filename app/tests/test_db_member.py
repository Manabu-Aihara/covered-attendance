import pytest

from app.models import User, Busho, Post
from app.routes_admin import get_user_role_list, get_user_role


# @pytest.mark.skip
def test_get_role_list(app_context):
    test_role_list = get_user_role_list()
    assert len(test_role_list) == 8


# @pytest.mark.skip
def test_get_user_role(app_context):
    test_result = get_user_role(Busho.NAME, Busho.CODE)
    assert test_result == ""
