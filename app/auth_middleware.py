# How To Authenticate Flask API Using JWT
# https://www.loginradius.com/blog/engineering/guest-post/securing-flask-api-with-jwt/
from functools import wraps
from typing import Dict, Any, Tuple
import importlib
from datetime import datetime, timedelta

import jwt
from flask import request, abort
from flask_login import current_user

from app import app, db
from app.models import StaffLoggin, Team, User
from app.dummy_model_todo import EventORM


def get_user_group_id() -> Tuple[int, int]:
    return (
        db.session.query(User.STAFFID, Team.CODE)
        .filter(User.STAFFID == current_user.STAFFID)
        .join(Team, Team.CODE == User.TEAM_CODE)
        .first()
    )


def get_user_group(group_code: int) -> Team:
    # return (
    #     db.session.query(Team)
    #     .filter(EventORM.staff_id == current_user.STAFFID)
    #     .join(Team, Team.CODE == group_code)
    #     .first()
    # )
    # こっちで良くない？
    return db.session.get(Team, group_code)


def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        # 以下コメントで、issue_tokenか!?
        # info = get_user_group_id()
        # token = issue_token(info.STAFFID, info.CODE)["data"]
        if "Authorization" in request.headers:
            # token = request.headers["Authorization"].split(" ")[1]
            # header_parts: list = token.split(".")
            # if len(header_parts) != 2 or header_parts[0].lower() != "bearer":
            #     print(type(header_parts[0]))
            # else:
            #     return {"message": "Request failed", "data": header_parts}, 401
            auth_header = request.headers["Authorization"]
            header_parts = auth_header.split(" ")
            if len(header_parts) != 2 or header_parts[0].lower() != "bearer":
                abort(401)
            # return header_parts[1]
            token = header_parts[1]
            print(f"Made toke: {token}")
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": token,
                "error": "Unauthorized",
            }, 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            # current_user = models.User().get_by_id(data["user_id"])
            """
                "__init__() missing 2 required positional arguments:
                'PASSWORD' and 'ADMIN'"
                """
            # group_idがない
            auth_user: StaffLoggin = (
                db.session.query(StaffLoggin)
                .filter(StaffLoggin.STAFFID == data["user_id"])
                .first()
            )
            # extension: int = data["group_id"]
            user_group_obj = get_user_group(data["group_id"])
            extension: str = user_group_obj.NAME
            if auth_user is None:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized",
                }, 401
            # これ入れると object is not subscriptable!?
            # if not auth_user["active"]:
            #     abort(403)
        except jwt.exceptions.DecodeError as e:
            print(f"JWT Exception: {e}")
            # importlib.reload(main)
            # print("リロードしたと思います")
            # return {
            #     "message": "No way",
            #     "data": auth_user.get_reset_token(),
            #     "error": str(e),
            # }
        except TypeError as e:
            print(f"staff id: {type(auth_user.STAFFID)}")
            return {
                "message": "Something went wrong",
                "data": isinstance(auth_user, StaffLoggin),
                "error": str(e),
                # "resource": dir(auth_user),
            }, 500
        else:
            # print(f"StaffLogin token: {auth_user.get_reset_token()}")
            return f(auth_user, extension, *args, **kwargs)

    return decorated


def issue_token(user_id: int, group_id: int) -> Dict[str, Any]:
    if current_user:
        payload = {"user_id": user_id, "group_id": group_id}
        # add token expiration time (5 seconds):
        payload["exp"] = datetime.now() + timedelta(hours=1)
        try:
            # token should expire after 24 hrs
            token = jwt.encode(
                payload,
                app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            return {"message": "Successfully fetched auth token", "data": token}
        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e),
                # "resource": token,
            }, 500
    else:
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized",
        }, 404
