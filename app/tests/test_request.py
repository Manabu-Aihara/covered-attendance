import pytest
import jwt

from app import db, app
from app.models import StaffLoggin
from app.auth_middleware import issue_token


# def test_get_request_in_confirm():
#     response = app.test_client().get('/confirm')
#     print(response.data)
#     assert response is not None


@pytest.fixture
def auth_user(app_context):
    auth_user20 = db.session.get(StaffLoggin, 20)
    # assert auth_user is not None
    # assert auth_user.STAFFID == 20
    return auth_user20


@pytest.fixture
def make_token(app_context, auth_user):
    token = jwt.encode(
        {"user_id": auth_user.STAFFID},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return token


def test_decode_token(app_context, make_token):
    dec_data = jwt.decode(make_token, app.config["SECRET_KEY"], algorithms=["HS256"])
    auth_user20 = db.session.get(StaffLoggin, dec_data["user_id"])

    assert isinstance(auth_user20, StaffLoggin)
    assert auth_user20.STAFFID == 20
