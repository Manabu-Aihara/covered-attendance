import os, math
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import wraps
from typing import List, TypeVar
import jpholiday

from dateutil.relativedelta import relativedelta
from monthdelta import monthmod

from flask import abort, flash, redirect, render_template, request, session
from flask.helpers import url_for
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_
from werkzeug.security import generate_password_hash
from werkzeug.urls import url_parse

from app import app, db, jimu_every_attendance, routes_attendance_option
from app.attendance_admin_classes import AttendanceAdminAnalysys
from app.calc_work_classes import (
    CalcTimeClass,
    DataForTable,
    TimeOffClass,
    get_last_date,
)
from app.calender_classes import MakeCalender
from app.forms import (
    AdminUserCreateForm,
    DelForm,
    EditForm,
    LoginForm,
    ResetPasswordForm,
    SaveForm,
    SelectMonthForm,
    UpdateForm,
)
from app.models import (
    CountAttendance,
    CounterForTable,
    RecordPaidHoliday,
    D_HOLIDAY_HISTORY,
    Post,
    Shinsei,
    StaffLoggin,
    TimeAttendance,
    Todokede,
    User,
    Busho,
    Jobtype,
    Team,
    KinmuTaisei,
    D_JOB_HISTORY,
    is_integer_num,
)
from app.common_func import GetPullDownList, ZeroCheck, GetData, GetDataS
from app.attendance_query_class import AttendanceQuery
from app.attendance_util import get_month_workday
from app.db_check_util import compare_db_item

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""######################################## 特別ページの最初の画面 ################################################"""


@app.route("/jimu_select_page", methods=["GET", "POST"])
@login_required
def jimu_select_page():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = current_user.STAFFID
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    select_page = [
        "オンコールチェック",
        "所属スタッフ出退勤確認",
        "出退勤集計(1日～末日）",
        "出退勤集計(26日～25日)",
    ]
    dat = ["0", "1", "2", "3"]

    if request.method == "POST":
        dat = request.form.get("select_page")
        if dat == "":
            return redirect(url_for("jimu_select_page", STAFFID=STAFFID))
        elif dat == "0":
            return redirect(url_for("jimu_oncall_count_26", STAFFID=STAFFID))
        elif dat == "1":
            return redirect(url_for("jimu_users_list", STAFFID=STAFFID))
        elif dat == "2":
            return redirect(url_for("jimu_summary_fulltime", startday=1))
        elif dat == "3":
            return redirect(url_for("jimu_summary_fulltime", startday=26))

    return render_template(
        "attendance/jimu_select_page.html",
        STAFFID=STAFFID,
        typ=typ,
        select_page=select_page,
        dat=dat,
        stf_login=stf_login,
    )


##### 常勤1日基準 #####
@app.route("/jimu_oncall_count_26/<STAFFID>", methods=["GET", "POST"])
@login_required
def jimu_oncall_count_26(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    dat = ["1", "2", "3", "4", "5", "6", "7"]

    form_month = SelectMonthForm()
    bumon = GetPullDownList(Busho, Busho.CODE, Busho.NAME, Busho.CODE)
    syozoku = GetPullDownList(Team, Team.CODE, Team.SHORTNAME, Team.CODE)
    syokusyu = GetPullDownList(
        Jobtype, Jobtype.JOBTYPE_CODE, Jobtype.SHORTNAME, Jobtype.JOBTYPE_CODE
    )
    keitai = GetPullDownList(
        KinmuTaisei,
        KinmuTaisei.CONTRACT_CODE,
        KinmuTaisei.NAME,
        KinmuTaisei.CONTRACT_CODE,
    )
    team = ""

    dwl_today = datetime.today()

    staffid = STAFFID
    jimu_usr = User.query.get(staffid)

    cfts = CounterForTable.query.all()

    # 　チームの絞り込みがある場合
    if form_month.validate_on_submit():
        if request.form.get("select_team") != "":
            team = int(request.form.get("select_team"))
            users = User.query.filter(
                User.JOBTYPE_CODE == 1, User.CONTRACT_CODE != 2, User.TEAM_CODE == team
            ).subquery()
        else:
            users = User.query.filter(
                User.JOBTYPE_CODE == 1, User.CONTRACT_CODE != 2
            ).subquery()
    else:
        users = User.query.filter(
            User.JOBTYPE_CODE == 1, User.CONTRACT_CODE != 2
        ).subquery()

    selected_workday = request.form.get("workday_nm")

    if selected_workday:
        y = datetime.strptime(selected_workday, "%Y-%m").year
        m = datetime.strptime(selected_workday, "%Y-%m").month
        session["workday_dat"] = selected_workday
        workday_dat = session["workday_dat"]
    else:
        y = datetime.today().year
        m = datetime.today().month
        workday_dat = datetime.today().strftime("%Y-%m")

    # オンコールカウント用　2次元配列
    OnCallCNT = [[0 for i in range(4)] for j in range(len(syozoku))]

    d = get_last_date(y, m)
    FromDay = date(y, m, 1)
    ToDay = date(y, m, d)

    # 土日オンコール分のカウントをJoinするために別Queryで作っておく(土日のオンコール持ってないとヒットしない。。。)
    Shinsei2 = (
        db.session.query(
            Shinsei.STAFFID, db.func.sum(Shinsei.ONCALL).label("OnCallHoliSum")
        )
        .filter(Shinsei.HOLIDAY == 1, Shinsei.WORKDAY.between(FromDay, ToDay))
        .group_by(Shinsei.STAFFID)
        .subquery()
    )

    # 対象年月日の職種や契約時間をスタッフごとに纏める(サブクエリ)
    JobHistory = (
        db.session.query(
            D_JOB_HISTORY.STAFFID,
            D_JOB_HISTORY.JOBTYPE_CODE,
            D_JOB_HISTORY.CONTRACT_CODE,
        )
        .filter(
            and_(
                D_JOB_HISTORY.START_DAY <= FromDay,
                D_JOB_HISTORY.END_DAY >= FromDay,
                D_JOB_HISTORY.CONTRACT_CODE != 2,
                D_JOB_HISTORY.JOBTYPE_CODE == 1,
            )
        )
        .subquery()
    )
    # 対象月のオンコールリスト取得
    shins = (
        db.session.query(
            Shinsei.STAFFID,
            User.LNAME,
            User.FNAME,
            User.TEAM_CODE,
            db.func.sum(Shinsei.ONCALL).label("OnCallSum"),
            db.func.sum(Shinsei.ONCALL_COUNT).label("OnCallActSum"),
            db.func.sum(Shinsei.ENGEL_COUNT).label("EngelSum"),
            Shinsei2.c.OnCallHoliSum,
        )
        .filter(
            Shinsei.WORKDAY.between(FromDay, ToDay),
            Shinsei.STAFFID == JobHistory.c.STAFFID,
            Shinsei.STAFFID == users.c.STAFFID,
        )
        .group_by(
            Shinsei.STAFFID,
            User.LNAME,
            User.FNAME,
            User.TEAM_CODE,
            Shinsei2.c.OnCallHoliSum,
        )
        .order_by(Shinsei.STAFFID)
        .join(User, Shinsei.STAFFID == User.STAFFID)
        .outerjoin(Shinsei2, Shinsei.STAFFID == Shinsei2.c.STAFFID)
    )

    # HTMLで一覧表示用
    StaffOnCall = [[0 for i in range(6)] for j in range(1)]

    if shins:
        for shin in shins:
            intOnCallholi = ZeroCheck(shin.OnCallHoliSum)
            StaffOnCall.append(
                [
                    shin.TEAM_CODE,
                    shin.LNAME + " " + shin.FNAME,
                    int(shin.OnCallSum) - int(intOnCallholi),
                    int(intOnCallholi),
                    int(shin.OnCallActSum),
                    int(shin.EngelSum),
                ]
            )

            # 2次元配列の0がオンコール当番カウント(平日) トータル用
            OnCallCNT[shin.TEAM_CODE][0] += int(shin.OnCallSum) - int(intOnCallholi)

            # 2次元配列の1がオンコール当番カウント(土日) トータル用
            OnCallCNT[shin.TEAM_CODE][1] += int(intOnCallholi)

            # 2次元配列の2がオンコール対応カウント トータル用
            OnCallCNT[shin.TEAM_CODE][2] += int(shin.OnCallActSum)

            # StaffOnCall[index][3] += int(shin.ONCALL_COUNT)
            OnCallCNT[shin.TEAM_CODE][3] += int(shin.EngelSum)

    return render_template(
        "attendance/jimu_oncall_count_26.html",
        typ=typ,
        form_month=form_month,
        workday_dat=workday_dat,
        y=y,
        m=m,
        dwl_today=dwl_today,
        users=users,
        cfts=cfts,
        bumon=bumon,
        syozoku=syozoku,
        syokusyu=syokusyu,
        keitai=keitai,
        jimu_usr=jimu_usr,
        STAFFID=staffid,
        dat=dat,
        team=team,
        stf_login=stf_login,
        lastday=d,
        OnCallCNT=OnCallCNT,
        StaffOnCall=StaffOnCall,
    )


T = TypeVar("T")


def get_more_condition_users(query_instances: List[T], *date_columun: str):
    today = datetime.today()
    result_users = []
    for query_instance in query_instances:
        try:
            date_c_name0: datetime = getattr(query_instance, date_columun[0])
            date_c_name1: datetime = getattr(query_instance, date_columun[1])
            # if date_c_name0 is None:
            #     raise TypeError("入職日の入力がありません")
            # if User.INDAY <= datetime.today()
            # Today 2024/8/23 if 2024/8/24 は入らない
            # if User.OUTDAY >= datetime.today()
            # Today 2024/8/23 if 2024/8/22 は入らない
            if date_c_name0 <= today:
                if (
                    date_c_name1 is None
                    or date_c_name1 > today
                    or (
                        date_c_name1.year == today.year
                        and date_c_name1.month >= today.month
                    )
                ):
                    result_users.append(query_instance)
        except TypeError:
            (
                print(f"{query_instance.STAFFID}: 入職日の入力がありません")
                if query_instance.STAFFID
                else print("入職日の入力がありません")
            )
            result_users.append(query_instance)

    return result_users


# date_c_name0.year == today.year and date_c_name0.month <= today.month


##### 常勤1日基準 ######
@app.route("/jimu_summary_fulltime/<startday>", methods=["GET", "POST"])
@login_required
def jimu_summary_fulltime(startday):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    form_month = SelectMonthForm()
    str_workday = "月選択をしてください。"
    bumon = GetData(Busho, Busho.CODE, Busho.NAME, Busho.CODE)
    syozoku = GetDataS(Team, Team.CODE, Team.SHORTNAME, Team.CODE)
    syokusyu = GetDataS(
        Jobtype, Jobtype.JOBTYPE_CODE, Jobtype.SHORTNAME, Jobtype.JOBTYPE_CODE
    )
    keitai = GetDataS(
        KinmuTaisei,
        KinmuTaisei.CONTRACT_CODE,
        KinmuTaisei.SHORTNAME,
        KinmuTaisei.CONTRACT_CODE,
    )
    POST = GetData(Post, Post.CODE, Post.NAME, Post.CODE)
    outer_display = 0
    jimu_usr = User.query.get(current_user.STAFFID)

    # users = User.query.all()
    # 後述

    cfts = CounterForTable.query.all()

    # sum_0 = 0
    # 全体のカウント、使えない
    # outer_workday_count = 0

    # 年月選択をしたかどうか
    selected_workday: str = ""
    # global y, m, workday_data
    if form_month.validate_on_submit():
        selected_workday = request.form.get("workday_name")  # 選択された日付

    print(f"Select month: {selected_workday}")
    y, m, workday_data = get_month_workday(selected_workday)
    # print(f"Select value: {workday_data}")

    d = get_last_date(y, m)
    if int(startday) != 1:
        # 1日開始以外の場合
        FromDay = date(y, m, int(startday)) - relativedelta(months=1)
        ToDay = date(y, m, 25)
    else:
        # 1日開始の場合
        FromDay = date(y, m, int(startday))
        ToDay = date(y, m, d)

    UserID = ""

    timeoff = 0
    halfway_through = 0

    counter_id_list = db.session.query(CounterForTable.STAFFID).all()
    for counter_id in counter_id_list:
        cftses = CounterForTable.query.get(counter_id.STAFFID)
        # print(f"Counter attribute: {cftses.__dict__}")

        cftses.ONCALL = 0
        cftses.ONCALL_HOLIDAY = 0
        cftses.ONCALL_COUNT = 0
        cftses.ENGEL_COUNT = 0
        cftses.NENKYU = 0
        cftses.NENKYU_HALF = 0
        cftses.TIKOKU = 0
        cftses.SOUTAI = 0
        cftses.KEKKIN = 0
        cftses.SYUTTYOU = 0
        cftses.SYUTTYOU_HALF = 0
        cftses.REFLESH = 0
        cftses.MILEAGE = 0
        cftses.SUM_WORKTIME = 0
        cftses.SUM_REAL_WORKTIME = 0
        cftses.OVERTIME = 0
        cftses.HOLIDAY_WORK = 0
        cftses.WORKDAY_COUNT = 0
        cftses.SUM_WORKTIME_10 = 0
        cftses.OVERTIME_10 = 0
        cftses.HOLIDAY_WORK_10 = 0
        cftses.TIMEOFF = 0
        cftses.HALFWAY_THROUGH = 0

        db.session.commit()

    attendace_qry_obj = AttendanceQuery(jimu_usr.STAFFID, FromDay, ToDay)
    clerical_attendance_list = attendace_qry_obj.get_clerical_attendance()

    for clerical_attendance in clerical_attendance_list:
        sh = clerical_attendance[0]

        # スタッフが変ったら
        # ここあまり好きじゃない、Unbound変数
        if UserID != sh.STAFFID:
            UserID = sh.STAFFID
            u = User.query.get(sh.STAFFID)
            cnt_for_tbl = CounterForTable.query.get(sh.STAFFID)
            rp_holiday = RecordPaidHoliday.query.get(sh.STAFFID)
            AttendanceDada = [["" for i in range(16)] for j in range(d + 1)]
            # 各スタッフのカウントになる、不思議
            workday_count = 0
            # sum_0 = 0
            """ 24/8/22 納得いかないまでも、追加した変数 """
            time_sum: int = 0
            # 各表示初期値
            oncall = []
            oncall_holiday = []
            oncall_cnt = []
            engel_cnt = []

            nenkyu = []
            nenkyu_half = []
            tikoku = []
            soutai = []
            kekkin = []
            syuttyou = []
            syuttyou_half = []
            reflesh = []
            s_kyori = []

            real_time = []
            real_time_sum = []
            syukkin_times_0 = []
            syukkin_holiday_times_0 = []
            over_time_0 = []

            timeoff1 = []
            timeoff2 = []
            timeoff3 = []
            halfway_through1 = []
            halfway_through2 = []
            halfway_through3 = []

        # if u.CONTRACT_CODE == 2:
        ##### １日基準 #####

        dft = DataForTable(
            y,
            m,
            d,
            sh.WORKDAY,
            sh.ONCALL,
            sh.HOLIDAY,
            sh.ONCALL_COUNT,
            sh.ENGEL_COUNT,
            sh.NOTIFICATION,
            sh.NOTIFICATION2,
            sh.MILEAGE,
            oncall,
            oncall_holiday,
            oncall_cnt,
            engel_cnt,
            nenkyu,
            nenkyu_half,
            tikoku,
            soutai,
            kekkin,
            syuttyou,
            syuttyou_half,
            reflesh,
            s_kyori,
            FromDay,
            ToDay,
        )
        dft.other_data()

        tm_off = TimeOffClass(
            y,
            m,
            d,
            sh.WORKDAY,
            sh.NOTIFICATION,
            sh.NOTIFICATION2,
            timeoff1,
            timeoff2,
            timeoff3,
            halfway_through1,
            halfway_through2,
            halfway_through3,
            FromDay,
            ToDay,
        )
        tm_off.cnt_time_off()

        dtm = datetime.strptime(sh.ENDTIME, "%H:%M") - datetime.strptime(
            sh.STARTTIME, "%H:%M"
        )
        # リアル実働時間
        real_time = dtm

        AttendanceDada[sh.WORKDAY.day][14] = 0
        settime = CalcTimeClass(
            dtm,
            sh.NOTIFICATION,
            sh.NOTIFICATION2,
            sh.STARTTIME,
            sh.ENDTIME,
            sh.OVERTIME,
            clerical_attendance.CONTRACT_CODE,
            AttendanceDada,
            over_time_0,
            real_time,
            real_time_sum,
            syukkin_holiday_times_0,
            sh.HOLIDAY,
            clerical_attendance.JOBTYPE_CODE,
            sh.STAFFID,
            sh.WORKDAY,
            clerical_attendance.HOLIDAY_TIME,
        )
        settime.calc_time()

        ##### データベース貯蔵 #####
        ln_oncall = len(oncall)
        ln_oncall_holiday = len(oncall_holiday)

        ln_oncall_cnt = 0
        for oc in oncall_cnt:
            if str.isnumeric(oc):
                ln_oncall_cnt += int(oc)

        ln_engel_cnt = 0
        for ac in engel_cnt:
            if str.isnumeric(ac):
                ln_engel_cnt += int(ac)

        ln_nenkyu = len(nenkyu)
        ln_nenkyu_half = len(nenkyu_half)
        ln_tikoku = len(tikoku)
        ln_soutai = len(soutai)
        ln_kekkin = len(kekkin)
        ln_syuttyou = len(syuttyou)
        ln_syuttyou_half = len(syuttyou_half)
        ln_reflesh = len(reflesh)

        ln_s_kyori = 0
        if s_kyori is not None:
            for s in s_kyori:
                ln_s_kyori += float(s)
            ln_s_kyori = math.floor(ln_s_kyori * 10) / 10

        # for n in range(len(syukkin_times_0)):
        #     if is_integer_num(syukkin_times_0[n]):
        #         print(f"出勤: {syukkin_times_0[n]}")
        #         sum_0 += syukkin_times_0[n]

        """ 24/8/22 変更分 """
        # ここで宣言された変数は“+=”不可
        # work_time_sum_60: float = 0.0
        # 🙅 work_time_sum_60 += AttendanceDada[sh.WORKDAY.day][14]

        time_sum += AttendanceDada[sh.WORKDAY.day][14]
        workday_count += 1 if time_sum != 0 else workday_count
        # print(f"{sh.STAFFID} aDd: {AttendanceDada[sh.WORKDAY.day][14]}")
        w_h = time_sum // (60 * 60)
        w_m = (time_sum - w_h * 60 * 60) / (60 * 60)
        # 実働時間計（１０進法）：10進数
        time_sum10 = w_h + w_m
        sum10_rnd = Decimal(time_sum10).quantize(Decimal("0.01"), ROUND_HALF_UP)

        w_m_60 = w_m * 60 / 100
        # 実労働時間計：60進数
        time_sum60 = w_h + w_m_60
        sum60_rnd = Decimal(time_sum60).quantize(Decimal("0.01"), ROUND_HALF_UP)
        # print(f"{sh.STAFFID} Sum: {time_sum10} {time_sum60}")

        """ 24/8/19 変更分 """
        # contract_work_time: float
        # if clerical_attendance.CONTRACT_CODE == 2:
        #     contract_work_time = clerical_attendance.PART_WORKTIME
        # else:
        #     work_time = (
        #         db.session.query(KinmuTaisei.WORKTIME)
        #         .filter(KinmuTaisei.CONTRACT_CODE == clerical_attendance.CONTRACT_CODE)
        #         .first()
        #     )
        #     contract_work_time = work_time.WORKTIME

        # if AttendanceDada[sh.WORKDAY.day][14] != 0:
        #     AttendanceDada[sh.WORKDAY.day][14] = contract_work_time
        #     workday_count += 1
        #     work_time_sum_10 = AttendanceDada[sh.WORKDAY.day][14] * workday_count
        # print(f"Count: {workday_count}")
        # working_time_10 = work_time_sum / (60 * 60)

        real_sum = 0
        for n in range(len(real_time_sum)):
            real_sum += real_time_sum[n]
        w_h = real_sum // (60 * 60)
        w_m = (real_sum - w_h * 60 * 60) // 60
        real_time = w_h + w_m / 100
        # real_time_10 = real_sum / (60 * 60)
        """ 24/8/20 変更分 """
        # w_m = (real_sum - w_h * 60 * 60) / (60 * 60)
        # real_time_lengthy = w_h + w_m
        # real_time = Decimal(real_time_lengthy).quantize(Decimal("0.1"), ROUND_HALF_UP)

        sum_over_0 = 0
        for n in range(len(over_time_0)):
            if not over_time_0[n]:
                sum_over_0 = sum_over_0
            else:
                sum_over_0 += over_time_0[n]
        o_h = sum_over_0 // (60 * 60)
        o_m = (sum_over_0 - o_h * 60 * 60) // 60
        over = o_h + o_m / 100
        over_10 = sum_over_0 / (60 * 60)

        sum_hol_0 = 0
        for t in syukkin_holiday_times_0:
            sum_hol_0 += t
        h_h = sum_hol_0 // (60 * 60)
        h_m = (sum_hol_0 - h_h * 60 * 60) // 60
        holiday_work = h_h + h_m / 100
        holiday_work_10 = sum_hol_0 / (60 * 60)

        # workday_count = len(syukkin_times_0)

        sum_timeoff1 = len(timeoff1)
        sum_timeoff2 = len(timeoff2)
        sum_timeoff3 = len(timeoff3)
        timeoff = sum_timeoff1 + sum_timeoff2 * 2 + sum_timeoff3 * 3

        sum_halfway_through1 = len(halfway_through1)
        sum_halfway_through2 = len(halfway_through2)
        sum_halfway_through3 = len(halfway_through3)
        halfway_through = (
            sum_halfway_through1 + sum_halfway_through2 * 2 + sum_halfway_through3 * 3
        )

        if cnt_for_tbl:
            cnt_for_tbl.ONCALL = ln_oncall
            cnt_for_tbl.ONCALL_HOLIDAY = ln_oncall_holiday
            cnt_for_tbl.ONCALL_COUNT = ln_oncall_cnt
            cnt_for_tbl.ENGEL_COUNT = ln_engel_cnt
            cnt_for_tbl.NENKYU = ln_nenkyu
            cnt_for_tbl.NENKYU_HALF = ln_nenkyu_half
            cnt_for_tbl.TIKOKU = ln_tikoku
            cnt_for_tbl.SOUTAI = ln_soutai
            cnt_for_tbl.KEKKIN = ln_kekkin
            cnt_for_tbl.SYUTTYOU = ln_syuttyou
            cnt_for_tbl.SYUTTYOU_HALF = ln_syuttyou_half
            cnt_for_tbl.REFLESH = ln_reflesh
            cnt_for_tbl.MILEAGE = ln_s_kyori
            cnt_for_tbl.SUM_WORKTIME = sum60_rnd
            cnt_for_tbl.SUM_REAL_WORKTIME = real_time
            cnt_for_tbl.OVERTIME = over
            cnt_for_tbl.HOLIDAY_WORK = holiday_work
            cnt_for_tbl.WORKDAY_COUNT = workday_count
            cnt_for_tbl.SUM_WORKTIME_10 = sum10_rnd
            cnt_for_tbl.OVERTIME_10 = over_10
            cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work_10
            cnt_for_tbl.TIMEOFF = timeoff
            cnt_for_tbl.HALFWAY_THROUGH = halfway_through

            db.session.commit()

            ##### 退職者表示設定

    # print(f"Date type: {type(User.INDAY)}")
    """ 24/8/27 変更 """
    clerk_totlling_filters = []
    if jimu_usr.TEAM_CODE != 1:
        clerk_totlling_filters.append(User.TEAM_CODE == jimu_usr.TEAM_CODE)
        # raise TypeError("Boolean value of this clause is not defined")
        # https://stackoverflow.com/questions/42681231/sqlalchemy-unexpected-results-when-using-and-and-or
        # filters.append(
        #     or_(User.OUTDAY == None, User.OUTDAY > datetime.today())
        # )
        # users_without_condition = (
        #     db.session.query(User).filter(and_(*clerk_totlling_filters)).all()
        # )
        # users = get_more_condition_users(users_without_condition, "INDAY", "OUTDAY")
        users = db.session.query(User).filter(and_(*clerk_totlling_filters)).all()
    else:
        users = db.session.query(User).all()

    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        "attendance/jimu_summary_fulltime_diff.html",
        startday=startday,
        typ=typ,
        form_month=form_month,
        workday_data=workday_data,
        y=y,
        m=m,
        dwl_today=datetime.today(),
        users=users,
        cfts=cfts,
        str_workday=str_workday,
        bumon=bumon,
        syozoku=syozoku,
        syokusyu=syokusyu,
        keitai=keitai,
        POST=POST,
        jimu_usr=jimu_usr,
        stf_login=stf_login,
        # workday_count=workday_count,
        timeoff=timeoff,
        halfway_rough=halfway_through,
        FromDay=FromDay,
        ToDay=ToDay,
        today=today,
    )


@app.route("/jimu_users_list/<STAFFID>", methods=["GET", "POST"])
@login_required
def jimu_users_list(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    # STAFFIDログインしてる人
    jimu_usr = User.query.get(STAFFID)

    base_user_list = (
        db.session.query(
            User.STAFFID, User.LNAME, User.FNAME, User.OUTDAY, KinmuTaisei.NAME
        ).join(KinmuTaisei, User.CONTRACT_CODE == KinmuTaisei.CONTRACT_CODE)
        # .filter(User.OUTDAY == None)
        # .all()
    )

    team_user_list = base_user_list.filter(User.TEAM_CODE == jimu_usr.TEAM_CODE).all()

    all_user_list = base_user_list.all()

    """ 2024/9/2 追加分 """
    caution_id_list = []
    exception_message = "テーブル間で、契約形態が合致していません"
    for user in all_user_list:
        unknown_value = compare_db_item(user.STAFFID)
        if isinstance(unknown_value, int):
            caution_id_list.append(unknown_value)

    """ 2024/7/19 追加機能分 """
    filters194 = []
    # if STAFFID == 194:
    filters194.append(User.DEPARTMENT_CODE == jimu_usr.DEPARTMENT_CODE)
    filters194.append(User.DEPARTMENT_CODE == 7)
    reference_user_list = base_user_list.filter(or_(*filters194)).all()
    # print(f"Members: {reference_user_list}")

    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        "attendance/jimu_users_list.html",
        jimu_usr=jimu_usr,
        team_u_lst=team_user_list,
        all_u=all_user_list,
        ref_lst=reference_user_list,
        today=today,
        cause_users=caution_id_list,
        exception=exception_message,
        stf_login=stf_login,
    )


@app.route("/jimu_users_select/<STAFFID>", methods=["GET", "POST"])
@login_required
def jimu_users_select(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    STAFFID = STAFFID
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)

    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()

    tbl_clm = [
        "日付",
        "曜日",
        "oncall",
        "oncall対応件数",
        "engel対応件数",
        "開始時間",
        "終了時間",
        "走行距離",
        "届出（午前）",
        "残業申請",
        "備考",
        "届出（午後）",
    ]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden"]
    typ = ["submit", "text", "time", "checkbox", "number", "date"]

    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get("workday_name"):
            workday_data_list = request.form.get("workday_name").split("-")
            session["workday_data"] = request.form.get("workday_name")
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])

        return redirect(url_for("jimu_users_attendance_edit", STAFFID=STAFFID))

    return render_template(
        "attendance/jimu_edit_users_attendance.html",
        title="ホーム",
        u=u,
        typ=typ,
        form_month=form_month,
        form=form,
        tbl_clm=tbl_clm,
        specification=specification,
        session=session,
        stf_login=stf_login,
    )


@app.route("/jimu_nenkyu_detail/<STAFFID>", methods=["GET", "POST"])
@login_required
def jimu_nenkyu_detail(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = STAFFID
    user = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    shinseis = Shinsei.query.filter(Shinsei.STAFFID == STAFFID).all()
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)

    next_datagrant = rp_holiday.NEXT_DATEGRANT - timedelta(days=1)

    ##### 今回付与日数 #####
    inday = rp_holiday.INDAY

    def nenkyu_days(a, h, s):

        if rp_holiday.LAST_DATEGRANT is None:
            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION == "3")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d") >= inday
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    nenkyu_all_days.add(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION == "4")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d") >= inday
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    nenkyu_half_days.add(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION == "16")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d") >= inday
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    seiri_days.append(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION2 == "4")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d") >= inday
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    nenkyu_half_days.add(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION2 == "16")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d") >= inday
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    seiri_days.append(shs.WORKDAY)

        else:
            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION == "3")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    >= rp_holiday.LAST_DATEGRANT
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    nenkyu_all_days.add(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION == "4")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    >= rp_holiday.LAST_DATEGRANT
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    nenkyu_half_days.add(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION == "16")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    >= rp_holiday.LAST_DATEGRANT
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    seiri_days.append(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION2 == "4")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    >= rp_holiday.LAST_DATEGRANT
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    nenkyu_half_days.add(shs.WORKDAY)

            shinseis = (
                Shinsei.query.filter(Shinsei.STAFFID == STAFFID)
                .filter(Shinsei.NOTIFICATION2 == "16")
                .all()
            )
            for shs in shinseis:
                if (
                    datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    >= rp_holiday.LAST_DATEGRANT
                    and datetime.strptime(shs.WORKDAY, "%Y-%m-%d")
                    < rp_holiday.NEXT_DATEGRANT
                ):
                    seiri_days.append(shs.WORKDAY)

        return nenkyu_all_days, nenkyu_half_days, seiri_days

    if inday.month == 4 and inday.month == 5:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 6 and inday.month == 7:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 8 and inday.month == 9:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 10 and inday.month == 11:
        first_day = inday.replace(month=4, day=1)
    elif inday.month == 12 and inday.month == 1:
        first_day = inday.replace(month=4, day=1)
    elif inday.month == 2 and inday.month == 3:
        first_day = inday.replace(month=4, day=1)

    ddm = monthmod(inday, datetime.today())[0].months
    dm = monthmod(inday, rp_holiday.LAST_DATEGRANT)[0].months

    """ 常勤 """
    if rp_holiday.CONTRACT_CODE != 2:

        ##### 年休付与日数設定 #####
        if inday.month == 4 or inday.month == 10:
            if ddm < 6:
                aquisition_days = 2
            elif ddm < 12:
                aquisition_days = 10
            elif dm < 24:
                aquisition_days = 11
            elif dm < 36:
                aquisition_days = 12
            elif dm < 48:
                aquisition_days = 14
            elif dm < 60:
                aquisition_days = 16
            elif dm < 76:
                aquisition_days = 18
            elif dm >= 76:
                aquisition_days = 20
        elif inday.month == 5 or inday.month == 11:
            if ddm < 5:
                aquisition_days = 2
            elif ddm < 11:
                aquisition_days = 10
            elif dm < 23:
                aquisition_days = 11
            elif dm < 35:
                aquisition_days = 12
            elif dm < 47:
                aquisition_days = 14
            elif dm < 59:
                aquisition_days = 16
            elif dm < 71:
                aquisition_days = 18
            elif dm >= 71:
                aquisition_days = 20
        elif inday.month == 6 or inday.month == 12:
            if ddm < 4:
                aquisition_days = 1
            elif ddm < 10:
                aquisition_days = 10
            elif dm < 22:
                aquisition_days = 11
            elif dm < 34:
                aquisition_days = 12
            elif dm < 46:
                aquisition_days = 14
            elif dm < 58:
                aquisition_days = 16
            elif dm < 70:
                aquisition_days = 18
            elif dm >= 70:
                aquisition_days = 20
        elif inday.month == 7 or inday.month == 1:
            if ddm < 3:
                aquisition_days = 1
            elif ddm < 9:
                aquisition_days = 10
            elif dm < 21:
                aquisition_days = 11
            elif dm < 33:
                aquisition_days = 12
            elif dm < 45:
                aquisition_days = 14
            elif dm < 57:
                aquisition_days = 16
            elif dm < 69:
                aquisition_days = 18
            elif dm >= 69:
                aquisition_days = 20
        elif inday.month == 8 or inday.month == 2:
            if ddm < 2:
                aquisition_days = 0
            elif ddm < 8:
                aquisition_days = 10
            elif dm < 20:
                aquisition_days = 11
            elif dm < 32:
                aquisition_days = 12
            elif dm < 44:
                aquisition_days = 14
            elif dm < 56:
                aquisition_days = 16
            elif dm < 68:
                aquisition_days = 18
            elif dm >= 68:
                aquisition_days = 20
        elif inday.month == 9 or inday.month == 3:
            if ddm < 1:
                aquisition_days = 0
            elif ddm < 7:
                aquisition_days = 10
            elif dm < 19:
                aquisition_days = 11
            elif dm < 31:
                aquisition_days = 12
            elif dm < 43:
                aquisition_days = 14
            elif dm < 55:
                aquisition_days = 16
            elif dm < 67:
                aquisition_days = 18
            elif dm >= 67:
                aquisition_days = 20

        ##### 繰越残日数２年消滅設定 #####
        if (
            monthmod(inday, datetime.today())[0].months == 24
            and rp_holiday.REMAIN_PAIDHOLIDAY >= 12
        ):
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
        elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
        elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
        elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
        elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
        elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
        elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
        elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20

        db.session.commit()
        enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER  # 使用可能日数

        ##### 取得日　取得日数　年休種類 #####
        nenkyu_all_days = set()
        nenkyu_half_days = set()
        seiri_days = set()

        nenkyu_days(nenkyu_all_days, nenkyu_half_days, seiri_days)

        x = (
            len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 + len(seiri_days) * 0.5
        )  # 年休使用日数

        if rp_holiday.USED_PAIDHOLIDAY is None:
            rp_holiday(USED_PAIDHOLIDAY=x)
            db.session.add(rp_holiday)
            db.session.commit()
        else:
            rp_holiday.USED_PAIDHOLIDAY = x
            db.session.commit()

        y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x  # 年休残日数
        if y < 0:
            y = 0

        """ パート """
    elif rp_holiday.CONTRACT_CODE == 2:

        aquisition_days = 0  # 簡易的に記載
        enable_days = 0  # 簡易的に記載

        ##### 取得日　取得日数　年休種類 #####
        nenkyu_all_days = set()
        nenkyu_half_days = set()
        seiri_days = set()

        nenkyu_days(nenkyu_all_days, nenkyu_half_days, seiri_days)

        x = (
            len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 + len(seiri_days) * 0.5
        )  # 年休使用日数

        if rp_holiday.USED_PAIDHOLIDAY is None:
            rp_holiday(USED_PAIDHOLIDAY=x)
            db.session.add(rp_holiday)
            db.session.commit()
        else:
            rp_holiday.USED_PAIDHOLIDAY = x
            db.session.commit()

        y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x  # 年休残日数
        if y < 0:
            y = 0

    return render_template(
        "attendance/jimu_nenkyu_detail.html",
        user=user,
        rp_holiday=rp_holiday,
        aquisition_days=aquisition_days,
        next_datagrant=next_datagrant,
        nenkyu_all_days=nenkyu_all_days,
        nenkyu_half_days=nenkyu_half_days,
        enable_days=enable_days,
        cnt_attendance=cnt_attendance,
        tm_attendance=tm_attendance,
        seiri_days=seiri_days,
        stf_login=stf_login,
    )
