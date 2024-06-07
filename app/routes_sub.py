import os
from datetime import datetime
from typing import List
import re

from flask import render_template, redirect, request, jsonify, make_response, url_for

from flask_login import current_user
from flask_login.utils import login_required
from flask_cors import CORS, cross_origin

from app import app, db
from app.auth_middleware import token_required, issue_token, get_user_group_id
from app.dummy_model_todo import TodoOrm, EventORM
from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog
from app.holiday_acquisition import HolidayAcquire

# 絶対こっち
origins = [os.getenv("CLOUD_TIMETABLE"), "http://localhost:5173"]
CORS(app, supports_credentials=True, origins=origins)
# app.config.update(SESSION_COOKIE_SAMESITE="None")
# CORS(app)


@app.route("/dummy-form/<target_id>", methods=["GET"])
@login_required
def appear_sub(target_id):
    recent_todo = TodoOrm.query.order_by(TodoOrm.id.desc()).first()
    return render_template(
        "admin/dummy.html", t_num=target_id, recent=recent_todo, stf_login=current_user
    )


@app.route("/todo/all", methods=["GET"])
# @login_required
@token_required
def print_all_todo(auth_user) -> List[TodoOrm]:

    td_dict_list = []
    todo_list: list = db.session.query(TodoOrm).all()
    for todo in todo_list:
        td_dict_list.append(todo.to_dict())

    return td_dict_list


# @app.route("/redirect")
# @login_required
# def redirect_func():
#     token_dict = issue_token(current_user.STAFFID)
#     # response.headers["Authorized"] = token["data"]
#     return redirect(url_for("post_access_token", token_data=token_dict["data"]))


@app.route("/timetable/auth", methods=["GET", "POST"])
@login_required
def post_access_token():
    user_group_id = get_user_group_id()
    token_dict = issue_token(user_group_id.STAFFID, user_group_id.CODE)
    # resp = make_response(jsonify(token_data))
    return redirect(f"http://localhost:5173/auth?token={token_dict['data']}")
    # github_page = os.getenv("GIT_PROVIDE")
    # return redirect(f"{github_page}/auth?token={token_dict['data']}")
    # cloud_site = os.getenv("CLOUD_TIMETABLE")
    # return redirect(f"{cloud_site}/auth?token={token_dict['data']}")


@app.route("/refresh", methods=["GET", "POST"])
# @login_required
@token_required
def refresh_token(auth_user, extension):
    new_token = issue_token(auth_user.STAFFID, extension)
    flask_resp = make_response(jsonify(new_token))

    return new_token["data"]


@app.route("/timetable/inquiry", methods=["GET", "POST"])
# @login_required
@token_required
def print_user_inquiry(auth_user, extension):
    return {"staff_id": str(auth_user.STAFFID), "group_id": str(extension)}


@app.route("/event/all", methods=["GET"])
@token_required
def get_all_event(auth_user, extension):
    event_dict_list = []
    event_list: list = db.session.query(EventORM).all()
    for event_item in event_list:
        event_dict_list.append(event_item.to_dict())

    return event_dict_list


def convert_strToDate(str_date: str):
    regex_data = re.sub(r"\.\d{3}Z", "", str_date)
    replaced_str_data = regex_data.replace("T", " ")
    print(f"変更Time: {replaced_str_data}")
    f = "%Y-%m-%d %H:%M:%S"
    # replaced_str_data = str_date.replace("T", " ").replace(".000Z", "")
    return datetime.strptime(replaced_str_data, f)


@app.route("/event/add", methods=["POST"])
@token_required
def append_event_item(auth_user, extension):
    event_item = EventORM()
    event_item.staff_id = request.json["staff_id"]
    event_item.group_id = request.json["group"]
    event_item.start_time = convert_strToDate(request.json["start_time"])
    event_item.end_time = convert_strToDate(request.json["end_time"])
    event_item.title = request.json["title"]
    db.session.add(event_item)
    db.session.commit()

    return redirect("/event/all")


@app.route("/event/update/<id>", methods=["POST"])
@token_required
def update_event_item(auth_user, extension, id: str):
    target_item = db.session.query(EventORM).filter(EventORM.id == int(id)).first()
    target_item.summary = request.json["summary"]
    target_item.progress = request.json["progress"]
    db.session.merge(target_item)
    db.session.commit()

    return redirect("/event/all")


@app.route("/event/remove/<id>", methods=["DELETE"])
@token_required
def remove_event_item(auth_user, extension, id: str):
    try:
        target_item = db.session.query(EventORM).filter(EventORM.id == int(id)).first()
        print(f"Delete: {isinstance(target_item, EventORM)}")
        db.session.delete(target_item)
        db.session.flush()
    except Exception as e:
        print(f"DB Exception: {e}")
        db.session.rollback()
    else:
        db.session.commit()

    return redirect("/event/all")


# 使わないかもAPI
@app.route("/date/update/<id>", methods=["POST"])
@token_required
def flush_date_item(auth_user, extension, id: str):
    target_item = db.session.query(EventORM).filter(EventORM.id == int(id)).first()
    target_item.start_time = request.json["start"]
    target_item.end_time = request.json["end"]
    print(f"DnD time: {target_item}")
    db.session.merge(target_item)
    db.session.flush()


@app.route("/date/update", methods=["POST"])
@token_required
def commit_date_item(auth_user, extension):
    json_data = request.json
    print(json_data["data"])
    for dict_data in json_data["data"]:
        try:
            target_item = (
                db.session.query(EventORM)
                .filter(EventORM.id == dict_data["id"])
                .first()
            )
            # print(convert_strToDate(dict_data["start"]))
            target_item.start_time = convert_strToDate(dict_data["start"])
            target_item.end_time = convert_strToDate(dict_data["end"])
            db.session.merge(target_item)
            db.session.flush()
        except Exception as e:
            print(f"DB Exception: {e}")
            db.session.rollback()
        else:
            db.session.commit()


def get_target_user_list(base_month: str) -> List[RecordPaidHoliday]:
    holiday_info_list = db.session.query(
        RecordPaidHoliday.STAFFID, RecordPaidHoliday.WORK_TIME
    ).all()

    month_target_list = []
    for holiday_info in holiday_info_list:
        holiday_acquire_obj = HolidayAcquire(holiday_info.STAFFID)
        if holiday_acquire_obj.convert_base_day().month == int(base_month):
            month_target_list.append(holiday_info)

    return month_target_list


@app.route("/holidays-form/<month>", methods=["GET"])
@login_required
# @auth_approval_user
def input_holiday_remains(month):
    # 入力必要項目は、残り日数、可能なら内時間休 -> D_PAIDHOLIDAY_LOG
    remain_exist_list = []
    for target_user in get_target_user_list(month):
        holiday_acquire_obj = HolidayAcquire(target_user.STAFFID)
        try:
            remain_exist_list.append(
                holiday_acquire_obj.print_remains() / target_user.WORK_TIME
            )
        except TypeError as e:
            print(e)
            remain_exist_list.append("")

        input_id_zip = zip(get_target_user_list(month), remain_exist_list)

    return render_template(
        "admin/before-acquisition.html",
        month=month,
        input_id_list=list(input_id_zip),
        stf_login=current_user,
    )


@app.route("/holidays-regist/<month>", methods=["POST"])
@login_required
def regist_before_acquisition(month):
    # 必要項目は、残り日数、可能なら内時間休
    # 必須出力項目は、年休付与タイプ
    remain_day_list: List[str] = request.form.getlist("remain_days")
    # 内時間休分
    sum_time_rest_list: List[str] = request.form.getlist("time_rests")
    for i, target_user in enumerate(get_target_user_list(month)):
        if sum_time_rest_list[i] != "":
            truncate_times: int = (
                target_user.WORK_TIME
                - int(sum_time_rest_list[i]) % target_user.WORK_TIME
            )
        else:
            truncate_times = 0
            # print(sum_time_rest_list[i])

        result_remain: float = (
            float(remain_day_list[i]) * target_user.WORK_TIME
        ) - truncate_times

        one_phl_data = PaidHolidayLog(
            target_user.STAFFID,
            result_remain,
            None,
            None,
            None,
            "年休システム稼働前入力",
        )
        print(truncate_times)
        db.session.add(one_phl_data)

    db.session.commit()

    return redirect("/")
