import os, math
import syslog
from typing import TypeVar
from datetime import date, datetime, timedelta
import time
import cProfile
import pstats
from decimal import ROUND_HALF_UP, Decimal
from functools import wraps
from collections import namedtuple
from typing import List, Dict, Optional
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
from app.calc_work_classes2 import (
    CalcTimeClass,
    CalcTimeFactory,
    get_last_date,
    output_rest_time,
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
from app.attendance_util import (
    get_month_workday,
    convert_null_role,
)
from app.db_check_util import compare_db_item, check_contract_value

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""######################################## 特別ページの最初の画面 ################################################"""


def pulldown_select_page(
    option_value: str, current_id: Optional[int], *args_pattern: int
):
    # To_page = namedtuple("To_page", ["url", "post_user_id", "start_day", "work_type"])
    # To_page.__new__.__defaults__ = (option_value, None, None, None)
    url_dict: Dict[int, str] = {
        "0": "jimu_select_page",
        "1": "jimu_oncall_count_26",
        "2": "jimu_users_list",
        "3": "jimu_summary_fulltime",
    }
    if option_value in ["0", "1", "2"]:
        return redirect(url_for(url_dict.get(option_value), STAFFID=current_id))
    else:
        print(f"Page args: {args_pattern[0]} {args_pattern[1]}")
        return redirect(
            url_for(
                url_dict.get("3"), startday=args_pattern[0], worktype=args_pattern[1]
            )
        )


@app.route("/jimu_select_page", methods=["GET", "POST"])
@login_required
def jimu_select_page():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    select_page: Dict[int, str] = {
        1: "オンコールチェック",
        2: "所属スタッフ出退勤確認",
        3: "常勤: 出退勤集計(1日～末日）",  # /1/1
        4: "パート: 出退勤集計(1日～末日）",  # /1/2
        5: "常勤: 出退勤集計(26日～25日)",  # /26/1
        6: "パート: 出退勤集計(26日～25日)",  # /26/2
    }

    if request.method == "POST":
        dat = request.form.get("select_page")
        if dat == "0" or dat == "1" or dat == "2":
            return pulldown_select_page(dat, current_id=current_user.STAFFID)
        elif dat == "3":
            return pulldown_select_page(dat, None, 1, 1)
        elif dat == "4":
            return pulldown_select_page(dat, None, 1, 2)
        elif dat == "5":
            return pulldown_select_page(dat, None, 26, 1)
        elif dat == "6":
            return pulldown_select_page(dat, None, 26, 2)

    return render_template(
        "attendance/jimu_select_page_diff.html",
        STAFFID=current_user.STAFFID,
        typ=typ,
        select_page=select_page,
        # dat=dat,
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


"""
    第2引数（退職日）が今日を過ぎていても、今月なら対象とする
    @Params:
        query_instances: list<T>
        date_columns: str
    @Return
        result_data_list: list<T> 
    """
T = TypeVar("T")


def get_more_condition_users(query_instances: list[T], date_columun: str) -> list[T]:
    today = datetime.today()
    result_data_list = []
    for query_instance in query_instances:
        # 退職日
        date_c_name1: datetime = getattr(query_instance, date_columun)
        # if date_c_name0 is None:
        #     TypeError出してくれる
        if (
            date_c_name1 is None
            # date_c_name0.year == today.year and date_c_name0.month <= today.month
            or date_c_name1 > today
            or (
                date_c_name1.year == today.year
                # ここの == だね
                and date_c_name1.month == today.month
            )
        ):
            result_data_list.append(query_instance)
        # except TypeError:
        #     (
        #         print(f"{query_instance.STAFFID}: 入職日の入力がありません")
        #         if query_instance.STAFFID
        #         else print("入職日の入力がありません")
        #     )
        #     result_data_list.append(query_instance)

    return result_data_list


##### 常勤1日基準 ######
@app.route("/jimu_summary_fulltime/<startday>/<worktype>", methods=["GET", "POST"])
@login_required
def jimu_summary_fulltime(startday, worktype):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    form_month = SelectMonthForm()
    str_workday = "月選択をしてください。"
    # bumon = GetData(Busho, Busho.CODE, Busho.NAME, Busho.CODE)
    # syozoku = GetDataS(Team, Team.CODE, Team.SHORTNAME, Team.CODE)
    # syokusyu = GetDataS(
    #     Jobtype, Jobtype.JOBTYPE_CODE, Jobtype.SHORTNAME, Jobtype.JOBTYPE_CODE
    # )
    # keitai = GetDataS(
    #     KinmuTaisei,
    #     KinmuTaisei.CONTRACT_CODE,
    #     KinmuTaisei.SHORTNAME,
    #     KinmuTaisei.CONTRACT_CODE,
    # )
    # POST = GetData(Post, Post.CODE, Post.NAME, Post.CODE)

    # from datetime import time は不可
    # パフォーマンス測定開始
    start_time = time.perf_counter()
    c_profile = cProfile.Profile()
    c_profile.enable()

    jimu_usr = User.query.get(current_user.STAFFID)
    # users = User.query.all()
    # 後述

    cfts = CounterForTable.query.all()

    # 年月選択をしたかどうか
    selected_workday: str = ""
    # global y, m, workday_data
    if form_month.validate_on_submit():
        selected_workday = request.form.get("workday_name")  # 選択された日付

    print(f"Select month: {selected_workday}")
    y, m = get_month_workday(selected_workday)
    disp_y_and_m = f"{y}-{m}"
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

    counter_id_list = db.session.query(CounterForTable.STAFFID).all()
    # 12/16 ここを抹消したい
    for counter_id in counter_id_list:
        cftses = CounterForTable.query.get(counter_id.STAFFID)

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

    print(f"Counters : {cfts}")

    # print(f"Date type: {type(User.INDAY)}")
    job_form: str
    attendace_qry_obj = AttendanceQuery(jimu_usr.STAFFID, FromDay, ToDay)
    if worktype == "1":
        job_form = "常勤"
        users_without_condition = db.session.query(User).filter(User.CONTRACT_CODE != 2)
        clerical_attendance_query = attendace_qry_obj.get_clerical_attendance(False)
    elif worktype == "2":
        job_form = "パート"
        users_without_condition = db.session.query(User).filter(User.CONTRACT_CODE == 2)
        clerical_attendance_query = attendace_qry_obj.get_clerical_attendance(True)

    if jimu_usr.TEAM_CODE != 1:
        # raise TypeError("Boolean value of this clause is not defined")
        # https://stackoverflow.com/questions/42681231/sqlalchemy-unexpected-results-when-using-and-and-or
        # filters.append(
        #     or_(User.OUTDAY == None, User.OUTDAY > datetime.today())
        # )
        users_without_condition = users_without_condition.filter(
            User.TEAM_CODE == jimu_usr.TEAM_CODE
        ).all()
        conditional_users = get_more_condition_users(users_without_condition, "OUTDAY")
    else:
        conditional_users = get_more_condition_users(users_without_condition, "OUTDAY")

    null_checked_users = []
    for conditional_user in users_without_condition:
        null_checked_users.append(convert_null_role(conditional_user))

    totalling_counter: int = 0

    # setting_time = CalcTimeClass(None, None, None, None, None, None)
    calc_time_factory = CalcTimeFactory()
    n_absence_list: List[str] = ["8", "17", "18", "19", "20"]
    for clerical_attendance in clerical_attendance_query:
        Shin = clerical_attendance[0]

        # スタッフが変ったら
        # ここあまり好きじゃない、Unbound変数
        if UserID != Shin.STAFFID:
            UserID = Shin.STAFFID
            cnt_for_tbl = CounterForTable.query.get(Shin.STAFFID)
            # cnt_for_tbl = CounterForTable()
            # AttendanceDada = [["" for i in range(16)] for j in range(d + 1)]
            # 各スタッフのカウントになる、不思議
            workday_count = 0
            """ 24/8/22 納得いかないまでも、追加した変数 """
            time_sum: float = 0.0
            # 各表示初期値
            real_time = []
            real_time_sum = []
            syukkin_times_0 = []
            syukkin_holiday_times_0 = []
            over_time_0 = []

            on_call_cnt: int = 0
            on_call_holiday_cnt: int = 0
            on_call_cnt_cnt: int = 0
            engel_int_cnt: int = 0

            holiday_cnt: int = 0
            half_holiday_cnt: int = 0
            late_cnt: int = 0
            leave_early_cnt: int = 0
            absence_cnt: int = 0
            trip_cnt: int = 0
            half_trip_cnt: int = 0
            reflesh_cnt: int = 0
            distance_sum: float = 0.0

            timeoff: int = 0
            halfway_through: int = 0

        # if u.CONTRACT_CODE == 2:
        ##### １日基準 #####

        on_call_holiday_cnt += (
            1 if Shin.ONCALL != "0" and Shin.WORKDAY.weekday() in [5, 6] else 0
        )
        on_call_cnt += (
            1 if Shin.ONCALL != "0" and Shin.WORKDAY.weekday() not in [5, 6] else 0
        )
        on_call_cnt_cnt += (
            int(Shin.ONCALL_COUNT)
            if not isinstance(Shin.ONCALL_COUNT, type(None))
            and Shin.ONCALL_COUNT != ""
            and Shin.ONCALL_COUNT != "0"
            else 0
        )
        engel_int_cnt += (
            int(Shin.ENGEL_COUNT)
            if not isinstance(Shin.ENGEL_COUNT, type(None))
            and Shin.ENGEL_COUNT != ""
            and Shin.ENGEL_COUNT != "0"
            else 0
        )
        distance_sum += (
            float(Shin.MILEAGE)
            if not isinstance(Shin.MILEAGE, type(None))
            and Shin.MILEAGE != ""
            and Shin.MILEAGE != "0.0"
            else 0
        )
        print(
            f"Count log1: {on_call_cnt} {on_call_cnt_cnt} {on_call_holiday_cnt} {engel_int_cnt}"
        )

        holiday_cnt += 1 if Shin.NOTIFICATION == "3" else 0
        half_holiday_cnt += (
            1 if Shin.NOTIFICATION == "4" or Shin.NOTIFICATION2 == "4" else 0
        )
        late_cnt += 1 if Shin.NOTIFICATION == "1" or Shin.NOTIFICATION2 == "1" else 0
        leave_early_cnt += (
            1 if Shin.NOTIFICATION == "2" or Shin.NOTIFICATION2 == "2" else 0
        )
        absence_cnt += 1 if Shin.NOTIFICATION in n_absence_list else 0
        trip_cnt += 1 if Shin.NOTIFICATION == "5" else 0
        half_trip_cnt += (
            1 if Shin.NOTIFICATION == "6" or Shin.NOTIFICATION2 == "6" else 0
        )
        reflesh_cnt += 1 if Shin.NOTIFICATION == "7" else 0
        print(
            f"Count log2: {holiday_cnt} {half_holiday_cnt} {late_cnt} {leave_early_cnt} {absence_cnt} {trip_cnt} {half_trip_cnt}"
        )

        # dtm = datetime.strptime(Shin.ENDTIME, "%H:%M") - datetime.strptime(
        #     Shin.STARTTIME, "%H:%M"
        # )
        # リアル実働時間
        # real_time = dtm
        # これを抹殺する
        # AttendanceDada[Shin.WORKDAY.day][14] = 0

        real_time_sum_append = real_time_sum.append
        over_time_append = over_time_0.append
        nurse_holiday_append = syukkin_holiday_times_0.append
        # setting_time.staff_id = Shin.STAFFID
        # setting_time.sh_starttime = Shin.STARTTIME
        # setting_time.sh_endtime = Shin.ENDTIME
        # setting_time.notifications = (
        #     Shin.NOTIFICATION,
        #     Shin.NOTIFICATION2,
        # )
        # setting_time.sh_overtime = Shin.OVERTIME
        # setting_time.sh_holiday = Shin.HOLIDAY
        setting_time = calc_time_factory.get_instance(Shin.STAFFID)
        setting_time.set_data(
            Shin.STARTTIME,
            Shin.ENDTIME,
            (Shin.NOTIFICATION, Shin.NOTIFICATION2),
            Shin.OVERTIME,
            Shin.HOLIDAY,
        )

        print(f"ID: {Shin.STAFFID}")
        actual_work_time = setting_time.get_actual_work_time()
        calc_real_time = setting_time.get_real_time()
        over_time = setting_time.get_over_time()
        nurse_holiday_work_time = setting_time.calc_nurse_holiday_work()
        # except TypeError as e:
        #     msg = f"{e}: {Shin.STAFFID}"
        #     return render_template(
        #         "error/403.html", title="Exception message", message=msg
        #     )
        # else:
        real_time_sum_append(calc_real_time)
        if Shin.OVERTIME == "1" and clerical_attendance.CONTRACT_CODE != 2:
            # over_time_0.append(over_time)
            over_time_append(over_time)
        if nurse_holiday_work_time != 9.99:
            # syukkin_holiday_times_0.append(nurse_holiday_work_time)
            nurse_holiday_append(nurse_holiday_work_time)

        print(f"{Shin.WORKDAY.day} 日")
        print(f"Real time: {calc_real_time}")
        print(f"Actual time: {actual_work_time}")
        print(f"Real time list: {real_time_sum}")
        print(f"Over time list: {over_time_0}")
        # print(f"Nurse holiday: {syukkin_holiday_times_0}")

        ##### データベース貯蔵 #####
        # ここで宣言された変数は“+=”不可
        # work_time_sum_60: float = 0.0
        # 🙅 work_time_sum_60 += AttendanceDada[Shin.WORKDAY.day][14]

        actual_second = actual_work_time.total_seconds()
        workday_count += 1 if actual_second != 0.0 else workday_count

        time_sum += actual_second
        time_sum_normal = time_sum / 3600
        # 実働時間計：10進数
        time_sum_rnd = Decimal(time_sum_normal).quantize(Decimal("0.01"), ROUND_HALF_UP)

        w_h = time_sum // (60 * 60)
        w_m = (time_sum - w_h * 60 * 60) // 60
        # 実労働時間計：60進数
        time_sum60 = w_h + w_m / 100

        real_sum: float = 0.0
        # for n in range(len(real_time_sum)):
        #     real_sum += real_time_sum[n]
        real_sum = sum(real_time_sum)
        w_h = real_sum // (60 * 60)
        w_m = (real_sum - w_h * 60 * 60) // 60
        # リアル労働時間計：60進数
        real_time = w_h + w_m / 100
        # real_time_10 = real_sum / (60 * 60)

        """ 24/8/20 変更分 """
        # w_m = (real_sum - w_h * 60 * 60) / (60 * 60)
        # real_time_lengthy = w_h + w_m
        # real_time = Decimal(real_time_lengthy).quantize(Decimal("0.01"), ROUND_HALF_UP)

        sum_over_0: float = 0.0
        # for n in range(len(over_time_0)):
        #     if not over_time_0[n]:
        #         sum_over_0 = sum_over_0
        #     else:
        #         sum_over_0 += over_time_0[n]
        sum_over_0 = sum(over_time_0)
        o_h = sum_over_0 // (60 * 60)
        o_m = (sum_over_0 - o_h * 60 * 60) // 60
        # 残業時間計：60進数
        over_60 = o_h + o_m / 100

        over_10 = sum_over_0 / (60 * 60)
        # 残業時間計：10進数
        over10_rnd = Decimal(over_10).quantize(Decimal("0.01"), ROUND_HALF_UP)

        sum_hol_0: float = 0.0
        # for t in syukkin_holiday_times_0:
        #     sum_hol_0 += t
        sum_hol_0 = sum(syukkin_holiday_times_0)
        h_h = sum_hol_0 // (60 * 60)
        h_m = (sum_hol_0 - h_h * 60 * 60) // 60
        # 看護師休日労働時間計：60進数
        holiday_work_60 = h_h + h_m / 100

        # 看護師休日労働時間計：10進数
        holiday_work_10 = sum_hol_0 / (60 * 60)
        holiday_work10_rnd = Decimal(holiday_work_10).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        sum_dict: Dict[str, int] = output_rest_time(
            Shin.NOTIFICATION, Shin.NOTIFICATION2
        )
        timeoff += sum_dict.get("Off")
        halfway_through += sum_dict.get("Through")
        # print(f"Inner time rest: {timeoff} {halfway_through}")
        print(f"Counter type: {isinstance(cnt_for_tbl, CounterForTable)}")

        if cnt_for_tbl:
            # cnt_for_tbl.STAFFID = Shin.STAFFID
            cnt_for_tbl.SUM_WORKTIME = time_sum60
            cnt_for_tbl.SUM_WORKTIME_10 = time_sum_rnd
            cnt_for_tbl.OVERTIME = over_60
            cnt_for_tbl.SUM_REAL_WORKTIME = real_time
            cnt_for_tbl.WORKDAY_COUNT = workday_count
            cnt_for_tbl.OVERTIME_10 = over10_rnd
            cnt_for_tbl.HOLIDAY_WORK = holiday_work_60
            cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work10_rnd
            cnt_for_tbl.ONCALL = on_call_cnt
            cnt_for_tbl.ONCALL_HOLIDAY = on_call_holiday_cnt
            cnt_for_tbl.ONCALL_COUNT = on_call_cnt_cnt
            cnt_for_tbl.ENGEL_COUNT = engel_int_cnt
            cnt_for_tbl.NENKYU = holiday_cnt
            cnt_for_tbl.NENKYU_HALF = half_holiday_cnt
            cnt_for_tbl.TIKOKU = late_cnt
            cnt_for_tbl.SOUTAI = leave_early_cnt
            cnt_for_tbl.KEKKIN = absence_cnt
            cnt_for_tbl.SYUTTYOU = trip_cnt
            cnt_for_tbl.SYUTTYOU_HALF = half_trip_cnt
            cnt_for_tbl.REFLESH = reflesh_cnt
            cnt_for_tbl.MILEAGE = distance_sum
            cnt_for_tbl.TIMEOFF = timeoff
            cnt_for_tbl.HALFWAY_THROUGH = halfway_through
            db.session.add(cnt_for_tbl)

        db.session.commit()

        totalling_counter += 1
    # for終わり
    # print(f"!!Outer time rest: {timeoff} {halfway_through}")

    today = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    # print(f"Totalling item count: {totalling_counter}")
    # print(f"Both length: {len(null_checked_users)} {len(cfts)}")
    # c_profile.disable()
    # c_stats = pstats.Stats(c_profile)
    # c_stats.sort_stats("cumtime").print_stats(20)

    end_time = time.perf_counter()
    run_time = end_time - start_time
    pref_result = f"{today}'| 実行時間'{str(run_time)}'秒'"
    print(pref_result)

    return render_template(
        "attendance/jimu_summary_fulltime.html",
        startday=startday,
        worktype=worktype,
        typ=typ,
        form_month=form_month,
        workday_data=disp_y_and_m,
        y=y,
        m=m,
        dwl_today=datetime.today(),
        # users=users,
        users=null_checked_users,
        cfts=cfts,
        str_workday=str_workday,
        # bumon=bumon,
        # syozoku=syozoku,
        # syokusyu=syokusyu,
        # keitai=keitai,
        # POST=POST,
        jimu_usr=jimu_usr,
        stf_login=stf_login,
        # workday_count=workday_count,
        # timeoff=timeoff,
        # halfway_rough=halfway_through,
        FromDay=FromDay,
        ToDay=ToDay,
        today=today,
        job_form=job_form,
    )


@app.route("/jimu_users_list/<STAFFID>", methods=["GET", "POST"])
@login_required
def jimu_users_list(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    # STAFFIDログインしてる人
    jimu_usr = User.query.get(STAFFID)

    base_user_list = (
        db.session.query(
            User.STAFFID,
            User.LNAME,
            User.FNAME,
            User.OUTDAY,
            User.DISPLAY,
            KinmuTaisei.NAME,
        ).join(KinmuTaisei, User.CONTRACT_CODE == KinmuTaisei.CONTRACT_CODE)
        # .filter(or_(User.OUTDAY == None, User.OUTDAY > datetime.today()))
        # .all()
    )

    team_user_list = base_user_list.filter(User.TEAM_CODE == jimu_usr.TEAM_CODE).all()

    all_user_list = base_user_list.all()

    """ 2024/9/2 追加分 """
    caution_id_list = []
    exception_message = "テーブル間で、契約形態が合致していません"
    for user in all_user_list:
        unknown_value = compare_db_item(user.STAFFID, check_contract_value)
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
    inday = user.INDAY

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
