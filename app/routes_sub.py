from typing import Tuple, List

from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required

from app import app, db
from app.dummy_model_todo import TodoOrm

from app.models import RecordPaidHoliday
from app.models_aprv import PaidHolidayLog
from app.routes_approvals import auth_approval_user
from app.holiday_acquisition import HolidayAcquire


@app.route("/dummy-form/<target_id>", methods=["GET"])
@login_required
def appear_sub(target_id):
    recent_todo = TodoOrm.query.order_by(TodoOrm.id.desc()).first()
    return render_template(
        "admin/dummy.html", t_num=target_id, recent=recent_todo, stf_login=current_user
    )


@app.route("/todo/add", methods=["POST"])
@login_required
def append_todo():
    summary = request.json["summary"]
    owner = request.json["owner"]
    one_todo = TodoOrm(summary=summary, owner=owner)
    db.session.add(one_todo)
    db.session.commit()

    return redirect("/dummy-form")


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
