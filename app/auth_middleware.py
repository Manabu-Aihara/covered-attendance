# How To Authenticate Flask API Using JWT
# https://www.loginradius.com/blog/engineering/guest-post/securing-flask-api-with-jwt/
from functools import wraps
from typing import Dict, Any
import json

import jwt
from flask import request, abort, jsonify
from flask_login import current_user

from app import app, db
from app.models import StaffLoggin

login_user = current_user


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 以下コメントで、issue_tokenか!?
        # token = None
        # if "Authorization" in request.headers:
        #     token = request.headers["Authorization"].split(" ")[1]
        # if not token:
        #     return {
        #         "message": "Authentication Token is missing!",
        #         "data": None,
        #         "error": "Unauthorized",
        #         # "resource": request.json,
        #     }, 401
        token = issue_token()["data"]
        token_parts = token.split(".")[1]
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            # current_user = models.User().get_by_id(data["user_id"])
            """
                "__init__() missing 2 required positional arguments: 'PASSWORD' and 'ADMIN'"
                """
            auth_user = db.session.get(StaffLoggin, data["user_id"])
            if auth_user is None:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized",
                }, 401
        #     if not auth_user["active"]:
        #         abort(403)
        except TypeError as e:
            return {
                "message": "Something went wrong",
                "data": isinstance(auth_user, StaffLoggin),
                "error": str(e),
                "resource": dir(auth_user),
            }, 500

        return f(auth_user, *args, **kwargs)

    return decorated


def issue_token() -> Dict[str, Any]:
    if current_user:
        try:
            # token should expire after 24 hrs
            token = jwt.encode(
                {"user_id": current_user.STAFFID},
                app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            return {"message": "Successfully fetched auth token", "data": token}
        except Exception as e:
            return {
                "error": "Something went wrong",
                "message": str(e),
                # "resource": user.STAFFID,
            }, 500
    else:
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized",
        }, 404
