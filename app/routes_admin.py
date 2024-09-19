"""
**********
勤怠システム
2022/04版
**********
"""

import os
import datetime
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from typing import List, Tuple, Dict
import jpholiday
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod

from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user, login_user, logout_user
from flask import abort
from sqlalchemy import and_, or_
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash

from app import app, db
from app import routes_admin_nenkyu, routes_admin_display_table
from app.forms import (
    LoginForm,
    AdminUserCreateForm,
    ResetPasswordForm,
    DelForm,
    UpdateForm,
    SaveForm,
    EditForm,
    AddDataUserForm,
    SelectMonthForm,
    DisplayForm,
)
from app.models import (
    User,
    Shinsei,
    StaffLoggin,
    Busho,
    KinmuTaisei,
    Post,
    Team,
    Jobtype,
    RecordPaidHoliday,
    CountAttendance,
    TimeAttendance,
    SystemInfo,
    CounterForTable,
    D_JOB_HISTORY,
    KinmuTaisei,
    Jobtype,
)
from app.attendance_admin_classes import AttendanceAdminAnalysys
from app.calender_classes import MakeCalender
from app.calc_work_classes import DataForTable, CalcTimeClass
from app.common_func import GetPullDownList, intCheck, blankCheck
from app.db_check_util import compare_db_item, check_contract_value

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 管理者か判断 *****"""


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)

    return decorated_view


"""***** 管理者関連 *****"""


@app.route("/admin")
@login_required
@admin_login_required
def home_admin():
    return render_template("admin/admin-home.html")


# ***** ユーザリストページ *****#
@app.route("/admin/users-list")
@login_required
@admin_login_required
def users_list_admin():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    users = StaffLoggin.query.all()
    us = User.query.all()

    return render_template(
        "admin/users-list-admin.html", users=users, us=us, stf_login=stf_login
    )


# ***** ユーザリストページ *****#
@app.route("/admin/edit_user_history/<STAFFID>/<int:ProcFlag>", methods=["GET", "POST"])
@login_required
@admin_login_required
def edit_user_history(STAFFID, ProcFlag):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    Contracts = (
        D_JOB_HISTORY.query.filter_by(STAFFID=STAFFID)
        .order_by(D_JOB_HISTORY.START_DAY)
        .all()
    )

    # 保存ボタンが押下されたらDB登録
    if ProcFlag == 1:

        # HTMLのForm情報取得
        JOBTYPE = request.form.getlist("Job")
        CONTYPE = request.form.getlist("con")
        PTIME = request.form.getlist("Pworktime")
        SDAY = request.form.getlist("StartDay")
        EDAY = request.form.getlist("EndDay")

        delHistory = D_JOB_HISTORY.query.filter_by(STAFFID=STAFFID).all()
        if delHistory:
            for row in delHistory:
                db.session.delete(row)
                db.session.flush()  # <-保留状態
        for num in range(1, len(JOBTYPE)):
            AddHISTORY = D_JOB_HISTORY(
                STAFFID,
                JOBTYPE[num],
                CONTYPE[num],
                blankCheck(PTIME[num]),
                blankCheck(SDAY[num]),
                blankCheck(EDAY[num]),
            )
            db.session.add(AddHISTORY)
        db.session.commit()

        dt_now = datetime.now()
        flash("保存しました。time[" + str(dt_now) + "]", "success")

    History = db.session.query(
        D_JOB_HISTORY,
        Jobtype.NAME.label("JOBNAME"),
        KinmuTaisei.NAME.label("CONTRACTNAME"),
    ).filter(
        and_(
            D_JOB_HISTORY.STAFFID == STAFFID,
            D_JOB_HISTORY.JOBTYPE_CODE == Jobtype.JOBTYPE_CODE,
            D_JOB_HISTORY.CONTRACT_CODE == KinmuTaisei.CONTRACT_CODE,
        )
    )

    ListJob = GetPullDownList(
        Jobtype, Jobtype.JOBTYPE_CODE, Jobtype.NAME, Jobtype.JOBTYPE_CODE
    )
    ListCon = GetPullDownList(
        KinmuTaisei,
        KinmuTaisei.CONTRACT_CODE,
        KinmuTaisei.NAME,
        KinmuTaisei.CONTRACT_CODE,
    )
    StaffInfo = StaffLoggin.query.filter_by(STAFFID=STAFFID).first()

    return render_template(
        "admin/user_history_edit.html",
        History=History,
        StaffInfo=StaffInfo,
        stf_login=stf_login,
        ListJob=ListJob,
        ListCon=ListCon,
    )


# ***** ユーザ登録ページ *****#
@app.route("/admin/create-user", methods=["GET", "POST"])
@login_required
@admin_login_required
def user_create_admin():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    mes = None
    form = AdminUserCreateForm()
    if form.validate_on_submit():
        STAFFID = form.staffid.data
        PASSWORD = form.password.data
        ADMIN = form.admin.data
        existing_username = StaffLoggin.query.filter_by(STAFFID=STAFFID).first()
        if existing_username:
            mes = "この社員番号は既に存在します。"
            flash("この社員番号は既に存在します。", "warning")

            return render_template("admin/user-create-admin.html", form=form, mes=mes)
        stl = StaffLoggin(STAFFID, PASSWORD, ADMIN)
        usr = User(STAFFID)
        rp_holiday = RecordPaidHoliday(STAFFID=STAFFID)
        sys_info = SystemInfo(STAFFID=STAFFID)
        cnt_attendance = CountAttendance(STAFFID=STAFFID)
        tm_attendance = TimeAttendance(STAFFID=STAFFID)
        cnt_for_tbl = CounterForTable(STAFFID=STAFFID)

        db.session.add(rp_holiday)
        db.session.add(cnt_attendance)
        db.session.add(tm_attendance)
        db.session.add(cnt_for_tbl)
        db.session.add(sys_info)
        db.session.add(stl)
        db.session.add(usr)
        db.session.commit()
        flash("続いて、追加のユーザデータを作成します", "info")

        return redirect(url_for("edit_data_user", STAFFID=STAFFID, intFlg=0))

    if form.errors:
        flash(form.errors, "danger")

    return render_template(
        "admin/user-create-admin.html", form=form, mes=mes, stf_login=stf_login
    )


"""
    @Params:
        query_name: str 実質返すクエリーのカラム名
        table_code: int DBテーブルコード
        user_code: int User内コード
    @Return:
        result_query: str DBテーブルコードから返す名称
        """


def get_user_role(query_name: str, table_code: int, user_code: int = 0) -> str:
    result_query = db.session.query(query_name).filter(table_code == user_code).first()
    if result_query is None:
        # リスト対応させるため、空の場合は空文字を返す
        result_query = ""
        return result_query
    else:
        return result_query[0]


"""
    DBから役職など5項目、dictのlistで返す
    @Return:
        list<dict<str, str>>
        """


def get_role_context(db_obj) -> Dict[str, str]:
    disp_department = get_user_role(Busho.NAME, Busho.CODE, db_obj.DEPARTMENT_CODE)
    dips_team = get_user_role(Team.SHORTNAME, Team.CODE, db_obj.TEAM_CODE)
    disp_contract = get_user_role(
        KinmuTaisei.NAME, KinmuTaisei.CONTRACT_CODE, db_obj.CONTRACT_CODE
    )
    disp_jobtype = get_user_role(
        Jobtype.SHORTNAME, Jobtype.JOBTYPE_CODE, db_obj.JOBTYPE_CODE
    )
    disp_post = get_user_role(Post.NAME, Post.CODE, db_obj.POST_CODE)

    return {
        "staff_id": db_obj.STAFFID,
        "department": disp_department,
        "team": dips_team,
        "contract": disp_contract,
        "job_type": disp_jobtype,
        "post": disp_post,
    }


# ***** ユーザ編集（リスト）ページ *****#
@app.route("/admin/edit_list_user", methods=["GET", "POST"])
@login_required
@admin_login_required
def edit_list_user():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()

    """ 2024/7/23 修正分 """
    # print(f"Decorator: {args}")
    user_infos = (
        db.session.query(User)
        # .filter(or_(User.OUTDAY == None, User.OUTDAY > datetime.today()))
        .all()
    )
    # user_infos = (
    #     db.session.query(User, D_JOB_HISTORY.JOBTYPE_CODE, D_JOB_HISTORY.CONTRACT_CODE)
    #     .outerjoin(D_JOB_HISTORY, D_JOB_HISTORY.STAFFID == User.STAFFID)
    #     .filter(or_(User.OUTDAY == None, User.OUTDAY > datetime.today()))
    #     .all()
    # )

    user_complete_list = []
    """ 24/9/2 追加機能 """
    caution_id_list: List[int] = []
    exception_message = "テーブル間で、契約形態及び職種が合致していません"
    # for user_info, jobtype_code, contract_code in user_infos:
    for user_info in user_infos:
        # compare_db_item(user_info.STAFFID)
        user_necessary_dict = {
            "family_name": user_info.LNAME,
            "first_name": user_info.FNAME,
            "family_kana": user_info.LKANA,
            "first_kana": user_info.FKANA,
            # 24/9/3 それに伴う変更
            # "job_type": get_user_role(
            #     Jobtype.SHORTNAME, Jobtype.JOBTYPE_CODE, jobtype_code
            # ),
            # "contract": get_user_role(
            #     KinmuTaisei.NAME, KinmuTaisei.CONTRACT_CODE, contract_code
            # ),
            "inday": user_info.INDAY,
            "outday": user_info.OUTDAY,
            "display": user_info.DISPLAY,
        }
        user_necessary_info = dict(**user_necessary_dict, **get_role_context(user_info))
        user_complete_list.append(user_necessary_info)

        unknown_value = compare_db_item(user_info.STAFFID, check_contract_value)
        if isinstance(unknown_value, int):
            caution_id_list.append(unknown_value)

    # print(user_complete_list)
    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    """ ここまで """

    if request.method == "POST":
        return redirect(url_for("edit_data_user", STAFFID=STAFFID))

    return render_template(
        "admin/edit_list_user.html",
        info_list=user_complete_list,
        today=today,
        cause_users=caution_id_list,
        exception=exception_message,
        stf_login=stf_login,
        # intFlg=1,
    )


# ***** ユーザ編集ページ *****#
@app.route("/admin/edit_data_user/<STAFFID>/<int:intFlg>", methods=["GET", "POST"])
@login_required
@admin_login_required
def edit_data_user(STAFFID, intFlg):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    form = AddDataUserForm()
    STAFFID = STAFFID
    u = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)
    cnt_for_tbl = CounterForTable.query.get(STAFFID)
    sys_info = SystemInfo.query.get(STAFFID)
    display_form = DisplayForm()

    if form.validate_on_submit():
        if form.department.data == 0:
            DEPARTMENT_CODE = 0
        else:
            DEPARTMENT_CODE = form.department.data

        if form.team.data == 0:
            TEAM_CODE = 0
        else:
            TEAM_CODE = form.team.data

        if form.contract.data == 0:
            CONTRACT_CODE = 0
        else:
            CONTRACT_CODE = form.contract.data

        if form.jobtype.data == 0:
            JOBTYPE_CODE = 0
        else:
            JOBTYPE_CODE = form.jobtype.data

        if form.post_code.data == 0:
            POST_CODE = 0
        else:
            POST_CODE = form.post_code.data

        if form.worker_time.data == "" or form.worker_time.data == None:
            WORKER_TIME = int("0")
        else:
            WORKER_TIME = int(form.worker_time.data)

        if (
            form.basetime_paidholiday.data == ""
            or form.basetime_paidholiday.data == None
        ):
            BASETIMES_PAIDHOLIDAY = float("0")
        else:
            BASETIMES_PAIDHOLIDAY = float(form.basetime_paidholiday.data)

        if form.last_carriedover.data == "" or form.last_carriedover.data == None:
            LAST_CARRIEDOVER = float("0")
        else:
            LAST_CARRIEDOVER = float(form.last_carriedover.data)

        if form.social.data == 0:
            SOCIAL_INSURANCE = 0
        else:
            SOCIAL_INSURANCE = form.social.data

        if form.employee.data == 0:
            EMPLOYMENT_INSURANCE = 0
        else:
            EMPLOYMENT_INSURANCE = form.employee.data
        EXPERIENCE = form.experi.data
        TABLET = form.tablet.data
        SINGLE = form.single.data
        SUPPORT = form.support.data
        HOUSE = form.house.data
        DISTANCE = form.distance.data
        LNAME = form.lname.data
        FNAME = form.fname.data
        LKANA = form.lkana.data
        FKANA = form.fkana.data
        POST = form.post.data
        ADRESS1 = form.adress1.data
        ADRESS2 = form.adress2.data
        TEL1 = form.tel1.data
        TEL2 = form.tel2.data
        BIRTHDAY = form.birthday.data
        INDAY = form.inday.data

        OUTDAY = form.outday.data
        STANDDAY = form.standday.data

        WORKER_TIME = form.worker_time.data
        BASETIMES_PAIDHOLIDAY = form.basetime_paidholiday.data

        REMARK = form.remark.data
        MAIL = form.m_a.data
        MAIL_PASS = form.ml_p.data
        MICRO_PASS = form.ms_p.data
        PAY_PASS = form.p_p.data
        KANAMIC_PASS = form.k_p.data
        ZOOM_PASS = form.z_p.data

        u.DEPARTMENT_CODE = DEPARTMENT_CODE
        u.TEAM_CODE = TEAM_CODE
        u.CONTRACT_CODE = CONTRACT_CODE
        u.JOBTYPE_CODE = JOBTYPE_CODE
        u.POST_CODE = POST_CODE
        u.LNAME = LNAME
        u.FNAME = FNAME
        u.LKANA = LKANA
        u.FKANA = FKANA
        u.POST = POST
        u.ADRESS1 = ADRESS1
        u.ADRESS2 = ADRESS2
        u.TEL1 = TEL1
        u.TEL2 = TEL2
        u.BIRTHDAY = BIRTHDAY
        u.INDAY = INDAY
        u.OUTDAY = OUTDAY
        u.STANDDAY = STANDDAY
        u.SOCIAL_INSURANCE = SOCIAL_INSURANCE
        u.EMPLOYMENT_INSURANCE = EMPLOYMENT_INSURANCE
        u.EMPLOYMENT_INSURANCE = EMPLOYMENT_INSURANCE
        u.EXPERIENCE = EXPERIENCE
        u.TABLET = TABLET
        u.SINGLE = SINGLE
        u.SUPPORT = SUPPORT
        u.HOUSE = HOUSE
        u.DISTANCE = DISTANCE
        u.REMARK = REMARK
        """ 24/9/12 追加 """
        print(f"Check: {display_form.display.data}")
        u.DISPLAY = display_form.display.data
        db.session.commit()

        rp_holiday.DEPARTMENT_CODE = DEPARTMENT_CODE
        rp_holiday.LNAME = LNAME
        rp_holiday.FNAME = FNAME
        rp_holiday.LKANA = LKANA
        rp_holiday.FKANA = FKANA
        rp_holiday.INDAY = INDAY
        # OUTDAYはM_RemainPaidHolidayにはない
        rp_holiday.TEAM_CODE = TEAM_CODE
        rp_holiday.CONTRACT_CODE = CONTRACT_CODE
        rp_holiday.DUMP_REFLESH = 0
        rp_holiday.DUMP_REFLESH_CHECK = 0

        rp_holiday.WORK_TIME = WORKER_TIME
        rp_holiday.BASETIMES_PAIDHOLIDAY = BASETIMES_PAIDHOLIDAY
        rp_holiday.LAST_CARRIEDOVER = LAST_CARRIEDOVER

        db.session.commit()

        sys_info.MAIL = MAIL
        sys_info.MAIL_PASS = MAIL_PASS
        sys_info.MICRO_PASS = MICRO_PASS
        sys_info.PAY_PASS = PAY_PASS
        sys_info.KANAMIC_PASS = KANAMIC_PASS
        sys_info.ZOOM_PASS = ZOOM_PASS
        db.session.commit()

        flash("ユーザ情報を編集しました", "info")
        return redirect(url_for("edit_list_user"))

    elif intFlg == 1:

        form.department.data = u.DEPARTMENT_CODE
        form.team.data = u.TEAM_CODE
        form.contract.data = u.CONTRACT_CODE
        form.jobtype.data = u.JOBTYPE_CODE
        form.post_code.data = u.POST_CODE
        form.lname.data = u.LNAME
        form.fname.data = u.FNAME
        form.lkana.data = u.LKANA
        form.fkana.data = u.FKANA
        form.post.data = u.POST
        form.adress1.data = u.ADRESS1
        form.adress2.data = u.ADRESS2
        form.tel1.data = u.TEL1
        form.tel2.data = u.TEL2
        form.birthday.data = u.BIRTHDAY
        form.inday.data = u.INDAY
        form.outday.data = u.OUTDAY
        form.standday.data = u.STANDDAY
        form.remark.data = u.REMARK
        form.m_a.data = sys_info.MAIL
        form.ml_p.data = sys_info.MAIL_PASS
        form.ms_p.data = sys_info.MICRO_PASS
        form.p_p.data = sys_info.PAY_PASS
        form.k_p.data = sys_info.KANAMIC_PASS
        form.z_p.data = sys_info.ZOOM_PASS
        form.worker_time.data = rp_holiday.WORK_TIME
        form.basetime_paidholiday.data = rp_holiday.BASETIMES_PAIDHOLIDAY
        form.last_carriedover.data = rp_holiday.LAST_CARRIEDOVER

        if u.SOCIAL_INSURANCE == 0:
            form.social.data = 0
        else:
            form.social.data = 1

        if u.EMPLOYMENT_INSURANCE == 0:
            form.employee.data = 0
        else:
            form.employee.data = 1

        if u.EXPERIENCE == 0 or u.EXPERIENCE is None:
            form.experi.data = 0
        else:
            form.experi.data = u.EXPERIENCE

        if u.TABLET == 0 or u.TABLET is None:
            form.tablet.data = 0
        else:
            form.tablet.data = u.TABLET

        if u.SINGLE == 0 or u.SINGLE is None:
            form.single.data = 0
        else:
            form.single.data = u.SINGLE

        if u.SUPPORT == 0 or u.SUPPORT is None:
            form.support.data = 0
        else:
            form.support.data = u.SUPPORT

        if u.HOUSE == 0 or u.HOUSE is None:
            form.house.data = 0
        else:
            form.house.data = u.HOUSE

        form.distance.data = u.DISTANCE
        """ 24/9/12 追加 """
        display_form.display.data = u.DISPLAY

    if form.errors:
        flash(form.errors, "danger")

    return render_template(
        "admin/edit_data_user_diff.html",
        form=form,
        disp_form=display_form,
        STAFFID=STAFFID,
        u=u,
        stf_login=stf_login,
        intFlg=intFlg,
    )


@app.route("/admin/delete-user/<STAFFID>")
@login_required
@admin_login_required
def user_delete_admin(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    stls = StaffLoggin.query.filter_by(STAFFID=STAFFID).all()
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    usrs = User.query.get(STAFFID)
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)
    cnt_for_tbl = CounterForTable.query.get(STAFFID)
    sys_info = SystemInfo.query.get(STAFFID)

    if shinseis:
        for sh in shinseis:
            db.session.delete(sh)
            db.session.commit()

    if stls:
        for st in stls:
            db.session.delete(st)
            db.session.commit()

    if rp_holiday:
        db.session.delete(rp_holiday)
        db.session.commit()

    if sys_info:
        db.session.delete(sys_info)
        db.session.commit()

    if cnt_attendance:
        db.session.delete(cnt_attendance)
        db.session.commit()

    if tm_attendance:
        db.session.delete(tm_attendance)
        db.session.commit()

    if cnt_for_tbl:
        db.session.delete(cnt_for_tbl)
        db.session.commit()

    if usrs:
        db.session.delete(usrs)
        db.session.commit()

    flash("ユーザを削除しました", "info")
    return redirect(url_for("home_admin"))


# ***** ユーザパスワードリセット *****#
@app.route("/admin/reset_password/<STAFFID>", methods=["GET", "POST"])
@login_required
@admin_login_required
def reset_token(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = STAFFID
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    u = User.query.get(STAFFID)

    hid_a = ""
    hid_b = "hidden"
    form = ResetPasswordForm()
    if form.validate_on_submit():
        STAFFID = STAFFID

        if form.PASSWORD.data != form.PASSWORD2.data:
            hid_a = "hidden"
            hid_b = ""
            return render_template(
                "attendance/reset_token.html",
                title="Reset Password",
                form=form,
                STAFFID=STAFFID,
                shinseis=shinseis,
                u=u,
                hid_a=hid_a,
                hid_b=hid_b,
            )
        elif form.PASSWORD.data == form.PASSWORD2.data:
            HASHED_PASSWORD = generate_password_hash(form.PASSWORD.data)
            ADMIN = form.ADMIN.data

            StaffLoggin.query.filter_by(STAFFID=STAFFID).update(
                dict(PASSWORD_HASH=HASHED_PASSWORD, ADMIN=ADMIN)
            )
            db.session.commit()

            return redirect(url_for("indextime", STAFFID=STAFFID, intFlg=1))

    if form.errors:
        flash("エラーが発生しました。")

    return render_template(
        "admin/reset_token.html",
        title="Reset Password",
        form=form,
        STAFFID=STAFFID,
        shinseis=shinseis,
        u=u,
        hid_a=hid_a,
        hid_b=hid_b,
        stf_login=stf_login,
    )
