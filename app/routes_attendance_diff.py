import os, math
from functools import wraps
from datetime import datetime, timedelta, date, time
from decimal import Decimal, ROUND_HALF_UP
import jpholiday
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod

from flask_login import logout_user
from flask_login import current_user, login_user
from flask import abort
from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login.utils import login_required
from sqlalchemy import and_
from werkzeug.security import generate_password_hash
from werkzeug.urls import url_parse

from app import app, db
from app import routes_attendance_option, jimu_oncall_count
from app.forms import (
    LoginForm,
    AdminUserCreateForm,
    ResetPasswordForm,
    DelForm,
    UpdateForm,
    SaveForm,
    SelectMonthForm,
)
from app.models import (
    User,
    Shinsei,
    StaffLoggin,
    Todokede,
    KinmuTaisei,
    RecordPaidHoliday,
    D_HOLIDAY_HISTORY,
    CountAttendance,
    TimeAttendance,
    D_JOB_HISTORY,
    M_TIMECARD_TEMPLATE,
    Team,
)
from app.attendance_classes import AttendanceAnalysys
from app.calender_classes import MakeCalender
from app.calc_work_classes import DataForTable, CalcTimeClass, get_last_date
from app.common_func import NoneCheck, TimeCheck, blankCheck, ZeroCheck

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 打刻ページ *****"""


@app.route("/indextime/<STAFFID>/<int:intFlg>", methods=["GET", "POST"])
@login_required
def indextime(STAFFID, intFlg):
    if app.permanent_session_lifetime == 0:
        return redirect(url_for("logout_mes"))

    u = User.query.get(STAFFID)
    # rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    cnt_attemdance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()

    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()

    tbl_clm = [
        "日付",
        "曜日",
        "oncall",
        "oncall対応件数",
        "angel対応件数",
        "開始時間",
        "終了時間",
        "走行距離",
        "届出<br>（午前）",
        "残業申請",
        "備考",
        "届出（午後）",
    ]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    d_week = {
        "Sun": "日",
        "Mon": "月",
        "Tue": "火",
        "Wed": "水",
        "Thu": "木",
        "Fri": "金",
        "Sat": "土",
    }
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden", "disabled"]
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    """
        24/7/25
        変更分
        """
    team_name = db.session.query(Team.NAME).all()

    ##### カレンダーとM_NOTIFICATION土日出勤の紐づけ関数 #####

    def get_day_of_week_jp(dt):
        w_list = ["", "", "", "", "", "1", "1"]
        return w_list[dt.weekday()]

    ##### 社員職種・勤務形態によるページ振り分け #####
    if STAFFID == 10000:
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = "hidden"
        bk = "hidden"
        othr = "hidden"
    elif u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
        oc = ""
        oc_cnt = ""
        eg = ""
        sk = "hidden"
        bk = ""
        othr = ""

    elif u.CONTRACT_CODE != 2 and (
        u.JOBTYPE_CODE == 3
        or u.JOBTYPE_CODE == 4
        or u.JOBTYPE_CODE == 5
        or u.JOBTYPE_CODE == 6
        or u.JOBTYPE_CODE == 7
        or u.JOBTYPE_CODE == 8
    ):
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = "hidden"
        othr = ""
        bk = ""

    else:
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = ""
        othr = ""
        bk = ""

    ##### M_NOTIFICATIONとindexの紐づけ #####
    td1 = Todokede.query.get(1)
    td2 = Todokede.query.get(2)
    td3 = Todokede.query.get(3)  # 年休（全日）はNotification2にはない
    td4 = Todokede.query.get(4)
    td5 = Todokede.query.get(5)  # 出張（全日）はNotification2にはない
    td6 = Todokede.query.get(6)
    td7 = Todokede.query.get(7)  # リフレッシュ休暇はNotification2にはない
    td8 = Todokede.query.get(8)  # 欠勤はNotification2にはない
    td9 = Todokede.query.get(9)
    td10 = Todokede.query.get(10)
    td11 = Todokede.query.get(11)
    td12 = Todokede.query.get(12)
    td13 = Todokede.query.get(13)
    td14 = Todokede.query.get(14)
    td15 = Todokede.query.get(15)
    td16 = Todokede.query.get(16)
    td17 = Todokede.query.get(17)
    td18 = Todokede.query.get(18)
    td19 = Todokede.query.get(19)
    td20 = Todokede.query.get(20)

    ##### 月選択の有無 #####
    # dsp_page = ""
    # 参照モードの場合、
    dsp_page = ""
    if intFlg == 3:
        # 参照モード
        dsp_page = "pointer-events: none;"

    if "y" in session:
        workday_data = session["workday_data"]
        y = session["y"]
        m = session["m"]

    # if datetime.today().month > 2:
    #     if datetime.today().year > int(session["y"]) or (datetime.today().year == int(session["y"]) and
    #                                                      datetime.today().month > int(session["m"]) + 1):
    # dsp_page = "pointer-events: none;"
    # dsp_page = ""
    # elif datetime.today().month == 1:
    #     if datetime.today().year > int(session["y"]) or (datetime.today().year - 1 == int(session["y"]) and int(session["m"]) <= 11):
    # dsp_page = "pointer-events: none;"
    # dsp_page = ""
    # else:
    #     if datetime.today().year > int(session["y"]):
    # dsp_page = "pointer-events: none;"
    # dsp_page = ""

    else:
        workday_data = datetime.today().strftime("%Y-%m-%d")
        y = datetime.now().year
        m = datetime.now().month

    ##### カレンダーの設定 #####
    cal = []
    hld = []

    mkc = MakeCalender(cal, hld, y, m)
    mkc.mkcal()

    template1 = 0
    template2 = 0

    onc = []
    onc_1 = []
    onc_2 = []
    onc_3 = []
    onc_4 = []
    onc_5 = []
    onc_6 = []
    onc_7 = []
    onc_8 = []

    s_kyori = []  ################################################## 使用
    syukkin_times_0 = []  ################################################# 使用
    syukkin_holiday_times_0 = []  ################################################# 使用
    real_time = []
    real_time_sum = []
    over_time_0 = []

    team = u.TEAM_CODE  # この職員のチームコード
    jobtype = u.JOBTYPE_CODE  # この職員の職種

    users = User.query.all()

    d = get_last_date(y, m)
    FromDay = date(y, m, 1)
    ToDay = date(y, m, d)
    shinseis = (
        db.session.query(Shinsei)
        .filter(
            and_(Shinsei.STAFFID == STAFFID, Shinsei.WORKDAY.between(FromDay, ToDay))
        )
        .all()
    )
    n = STAFFID

    # 出退勤テンプレートの取得(月途中で契約変更された場合の考慮)
    template = (
        db.session.query(M_TIMECARD_TEMPLATE.TEMPLATE_NO)
        .filter(
            and_(
                D_JOB_HISTORY.STAFFID == STAFFID,
                D_JOB_HISTORY.START_DAY <= FromDay,
                D_JOB_HISTORY.END_DAY >= ToDay,
                D_JOB_HISTORY.JOBTYPE_CODE == M_TIMECARD_TEMPLATE.JOBTYPE_CODE,
                D_JOB_HISTORY.CONTRACT_CODE == M_TIMECARD_TEMPLATE.CONTRACT_CODE,
            )
        )
        .group_by(M_TIMECARD_TEMPLATE.TEMPLATE_NO)
    )
    # 月の途中の契約変更1回までは対応
    for templates in template:
        if template1 == 0:
            template1 = templates.TEMPLATE_NO
        else:
            template2 = templates.TEMPLATE_NO

    shinseis = (
        db.session.query(
            Shinsei.STAFFID,
            Shinsei.STARTTIME,
            Shinsei.ENDTIME,
            Shinsei.WORKDAY,
            Shinsei.HOLIDAY,
            Shinsei.OVERTIME,
            Shinsei.NOTIFICATION,
            Shinsei.NOTIFICATION2,
            Shinsei.ONCALL,
            Shinsei.ENGEL_COUNT,
            Shinsei.MILEAGE,
            Shinsei.ONCALL_COUNT,
            Shinsei.ENGEL_COUNT,
            Shinsei.ALCOHOL,
            Shinsei.REMARK,
            User.FNAME,
            User.LNAME,
            D_JOB_HISTORY.JOBTYPE_CODE,
            D_JOB_HISTORY.CONTRACT_CODE,
            M_TIMECARD_TEMPLATE.TEMPLATE_NO,
        )
        .filter(
            and_(
                Shinsei.STAFFID == STAFFID,
                Shinsei.STAFFID == User.STAFFID,
                Shinsei.WORKDAY.between(FromDay, ToDay),
                Shinsei.STAFFID == D_JOB_HISTORY.STAFFID,
                D_JOB_HISTORY.START_DAY <= Shinsei.WORKDAY,
                D_JOB_HISTORY.END_DAY >= Shinsei.WORKDAY,
                D_JOB_HISTORY.JOBTYPE_CODE == M_TIMECARD_TEMPLATE.JOBTYPE_CODE,
                D_JOB_HISTORY.CONTRACT_CODE == M_TIMECARD_TEMPLATE.CONTRACT_CODE,
            )
        )
        .order_by(Shinsei.WORKDAY)
    )

    length_oncall = len(onc)
    length_oncall_1 = len(onc_1)
    length_oncall_2 = len(onc_2)
    length_oncall_3 = len(onc_3)
    length_oncall_4 = len(onc_4)
    length_oncall_5 = len(onc_5)
    length_oncall_6 = len(onc_6)
    length_oncall_7 = len(onc_7)
    length_oncall_8 = len(onc_8)

    reload_y = ""
    ##### 保存ボタン押下処理（１日始まり） 打刻ページ表示で使用 #####
    if form.validate_on_submit():

        # 削除処理
        delAttendance = db.session.query(Shinsei).filter(
            and_(Shinsei.STAFFID == STAFFID, Shinsei.WORKDAY.between(FromDay, ToDay))
        )
        if delAttendance:
            for row in delAttendance:
                db.session.delete(row)
                db.session.flush()  # <-保留状態
                # print(f"消滅します {row.id}")

        reload_y = request.form.get("reload_h")
        ##### データ取得 #####
        i = 0
        for c in cal:
            data0 = request.form.get("dat" + str(i))  # フラッグID
            data1 = request.form.get("row" + str(i))  # 日付
            data2 = TimeCheck(request.form.get("stime" + str(i)))  # 開始時間
            data3 = TimeCheck(request.form.get("ftime" + str(i)))  # 終了時間
            data_4 = request.form.get("skyori" + str(i))  # 移動距離
            data5 = request.form.get("oncall" + str(i))  # オンコール
            data6 = request.form.get("oncall_cnt" + str(i))  # オンコール回数
            data7 = request.form.get("todokede" + str(i))  # 届出AM
            data8 = request.form.get("zangyou" + str(i))  # 残業
            data9 = request.form.get("engel" + str(i))  # エンゼル回数
            data10 = request.form.get("bikou" + str(i))  # 備考
            data11 = request.form.get("todokede_pm" + str(i))  # 届出PM
            data12 = request.form.get("alcohol" + str(i))  # 届出PM

            ##### 勤怠条件分け #####
            InsertFlg = 0
            atd = AttendanceAnalysys(
                c,
                data0,
                data1,
                data2,
                data3,
                data_4,
                data5,
                data6,
                data7,
                data8,
                data9,
                data10,
                data11,
                data12,
                STAFFID,
                InsertFlg,
            )
            atd.analysys()

            ##### 走行距離小数第1位表示に変換 #####
            if data_4 is not None and data_4 != "":
                ZEN = "".join(chr(0xFF01 + j) for j in range(94))
                HAN = "".join(chr(0x21 + k) for k in range(94))
                ZEN2HAN = str.maketrans(ZEN, HAN)
                data__4 = data_4.translate(ZEN2HAN)

                def is_num(s):
                    try:
                        float(s)
                    except ValueError:
                        return flash("数字以外は入力できません。")
                    else:
                        return s

                data___4 = is_num(data__4)

                data4 = str(
                    Decimal(data___4).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                )
            else:
                data4 = None

            if data5 == "on":
                oncall = 1
            else:
                oncall = 0

            if data6 != "0":
                oncall_cnt = data6
            elif data6 == "" or data6 == "0":
                oncall_cnt = "0"

            todokede = data7

            if data8 == "on":
                zangyou = 1
            else:
                zangyou = 0

            if data9 != "0":
                engel = data9
            elif data9 == "" or data9 == "0":
                engel = "0"

            holiday = ""
            if jpholiday.is_holiday_name(datetime.strptime(data1, "%Y-%m-%d")):
                holiday = "2"
            elif get_day_of_week_jp(datetime.strptime(data1, "%Y-%m-%d")) == "1":
                holiday = "1"

            if data12 == "on":
                alc = 1
            else:
                alc = 0

            todokede_PM = data11

            # 登録するかの判定
            # 開始時間
            if data2 != "00:00":
                InsertFlg = 1
            elif data3 != "00:00":
                InsertFlg = 1
            elif data4 is not None and data4 != "0.0" and data4 != "":
                InsertFlg = 1
            elif data5 == "on":
                InsertFlg = 1
            elif blankCheck(data7) is not None:
                InsertFlg = 1
            elif blankCheck(data11) is not None:
                InsertFlg = 1
            elif blankCheck(data12) is not None:
                InsertFlg = 1
            elif blankCheck(oncall_cnt) is not None:
                InsertFlg = 1
            elif blankCheck(data9) is not None:
                InsertFlg = 1
            elif data10 != "":
                InsertFlg = 1

            if InsertFlg == 1:

                AddATTENDANCE = Shinsei(
                    STAFFID,
                    data1,
                    holiday,
                    data2,
                    data3,
                    data_4,
                    oncall,
                    oncall_cnt,
                    engel,
                    data7,
                    todokede_PM,
                    zangyou,
                    alc,
                    data10,
                )

                db.session.add(AddATTENDANCE)

            i = i + 1

        db.session.commit()

    # 配列に初期値入れてデータの存在するとこに入れる
    # オンコールカウント用　2次元配列
    AttendanceDada = [["" for i in range(16)] for j in range(d + 1)]

    # 初期値
    i = 1
    for c in cal:
        # print(f"*: {c}")
        #
        # AttendanceDada[i][1] = datetime.strptime(str(y, m, i), "%Y-%m-%d")
        # 日付(YYYY-MM-DD)
        AttendanceDada[i][1] = c.strftime("%Y-%m-%d")
        # 日付(DD)
        AttendanceDada[i][2] = c.strftime("%d")
        # 曜日(日本語)
        AttendanceDada[i][3] = d_week[c.strftime("%a")]
        # オンコール当番
        # オンコール対応
        # エンゼル対応
        # 開始時間
        AttendanceDada[i][7] = "00:00"
        # 終了時間
        AttendanceDada[i][8] = "00:00"
        # 走行距離
        AttendanceDada[i][9] = 0.0
        # 申請(AM)
        # 申請(PM)
        # 残業申請
        # アルコールチェック
        # 勤務時間
        AttendanceDada[i][14] = 0
        # 備考
        i = i + 1

    Parttime = (
        db.session.query(
            D_HOLIDAY_HISTORY.STAFFID, Shinsei.WORKDAY, D_HOLIDAY_HISTORY.HOLIDAY_TIME
        )
        .filter(
            and_(
                Shinsei.STAFFID == STAFFID,
                Shinsei.STAFFID == D_HOLIDAY_HISTORY.STAFFID,
                Shinsei.WORKDAY.between(FromDay, ToDay),
                Shinsei.STAFFID == D_HOLIDAY_HISTORY.STAFFID,
                D_HOLIDAY_HISTORY.START_DAY <= Shinsei.WORKDAY,
                D_HOLIDAY_HISTORY.END_DAY >= Shinsei.WORKDAY,
            )
        )
        .subquery()
    )

    shinseis = (
        (
            db.session.query(
                Shinsei.STAFFID,
                Shinsei.STARTTIME,
                Shinsei.ENDTIME,
                Shinsei.WORKDAY,
                Shinsei.HOLIDAY,
                Shinsei.OVERTIME,
                Shinsei.NOTIFICATION,
                Shinsei.NOTIFICATION2,
                Shinsei.ONCALL,
                Shinsei.ENGEL_COUNT,
                Shinsei.MILEAGE,
                Shinsei.ALCOHOL,
                Shinsei.REMARK,
                Shinsei.ONCALL_COUNT,
                Shinsei.ENGEL_COUNT,
                User.FNAME,
                User.LNAME,
                D_JOB_HISTORY.JOBTYPE_CODE,
                D_JOB_HISTORY.CONTRACT_CODE,
                D_JOB_HISTORY.PART_WORKTIME,  # 24/8/16 追加クエリー
                Parttime.c.HOLIDAY_TIME,
                M_TIMECARD_TEMPLATE.TEMPLATE_NO,
            ).filter(
                and_(
                    Shinsei.STAFFID == STAFFID,
                    Shinsei.STAFFID == User.STAFFID,
                    Shinsei.WORKDAY.between(FromDay, ToDay),
                    Shinsei.STAFFID == D_JOB_HISTORY.STAFFID,
                    D_JOB_HISTORY.START_DAY <= Shinsei.WORKDAY,
                    D_JOB_HISTORY.END_DAY >= Shinsei.WORKDAY,
                    D_JOB_HISTORY.JOBTYPE_CODE == M_TIMECARD_TEMPLATE.JOBTYPE_CODE,
                    D_JOB_HISTORY.CONTRACT_CODE == M_TIMECARD_TEMPLATE.CONTRACT_CODE,
                )
            )
        )
        .outerjoin(
            Parttime,
            and_(
                Parttime.c.STAFFID == Shinsei.STAFFID,
                Parttime.c.WORKDAY == Shinsei.WORKDAY,
            ),
        )
        .order_by(Shinsei.STAFFID, Shinsei.WORKDAY)
    )

    # sum_0 = 0
    workday_count = 0
    """ 24/8/16 追加変数 """
    work_time_sum: float = 0.0
    for Shin in shinseis:
        # 日付
        # 曜日
        # 勤務日
        # オンコール当番
        AttendanceDada[Shin.WORKDAY.day][4] = Shin.ONCALL
        # オンコール対応
        AttendanceDada[Shin.WORKDAY.day][5] = NoneCheck(Shin.ONCALL_COUNT)
        # エンゼル対応
        AttendanceDada[Shin.WORKDAY.day][6] = NoneCheck(Shin.ENGEL_COUNT)
        # 開始時間
        AttendanceDada[Shin.WORKDAY.day][7] = TimeCheck(Shin.STARTTIME)
        # 終了時間
        AttendanceDada[Shin.WORKDAY.day][8] = TimeCheck(Shin.ENDTIME)
        # 走行距離
        AttendanceDada[Shin.WORKDAY.day][9] = Shin.MILEAGE
        # 申請(AM)
        AttendanceDada[Shin.WORKDAY.day][10] = Shin.NOTIFICATION
        # 申請(PM)
        AttendanceDada[Shin.WORKDAY.day][11] = Shin.NOTIFICATION2
        # 残業申請
        AttendanceDada[Shin.WORKDAY.day][12] = Shin.OVERTIME
        # アルコールチェック
        AttendanceDada[Shin.WORKDAY.day][13] = Shin.ALCOHOL
        # 備考
        AttendanceDada[Shin.WORKDAY.day][15] = Shin.REMARK

        # 参照モード
        dtm = datetime.strptime(Shin.ENDTIME, "%H:%M") - datetime.strptime(
            Shin.STARTTIME, "%H:%M"
        )
        real_time = dtm
        # 常勤看護師の場合

        settime = CalcTimeClass(
            dtm,
            Shin.NOTIFICATION,
            Shin.NOTIFICATION2,
            Shin.STARTTIME,
            Shin.ENDTIME,
            Shin.OVERTIME,
            Shin.CONTRACT_CODE,
            AttendanceDada,
            over_time_0,
            real_time,
            real_time_sum,
            syukkin_holiday_times_0,
            Shin.HOLIDAY,
            Shin.JOBTYPE_CODE,
            STAFFID,
            Shin.WORKDAY,
            Shin.HOLIDAY_TIME,
        )
        settime.calc_time()

        contract_work_time: float
        if Shin.CONTRACT_CODE == 2:
            contract_work_time = Shin.PART_WORKTIME
        else:
            work_time = (
                db.session.query(KinmuTaisei.WORKTIME)
                .filter(KinmuTaisei.CONTRACT_CODE == Shin.CONTRACT_CODE)
                .first()
            )
            contract_work_time = work_time.WORKTIME

        # sum_0 += AttendanceDada[Shin.WORKDAY.day][14]
        # if AttendanceDada[Shin.WORKDAY.day][14] > 0:
        #     workday_count += 1

        # w_h = AttendanceDada[Shin.WORKDAY.day][14] // (60 * 60)
        # """ 24/8/1 修正分 """
        # w_m = (AttendanceDada[Shin.WORKDAY.day][14] - w_h * 60 * 60) / (60 * 60)
        # AttendanceDada[Shin.WORKDAY.day][14] = w_h + w_m
        """ 24/8/16 追加(勤務時間合計、残業考慮なしver) """
        if (
            AttendanceDada[Shin.WORKDAY.day][7] != "00:00"
            and AttendanceDada[Shin.WORKDAY.day][8] is not None
        ):
            AttendanceDada[Shin.WORKDAY.day][14] = contract_work_time
            # if AttendanceDada[Shin.WORKDAY.day][14] != 0:
            workday_count += 1
            work_time_sum = AttendanceDada[Shin.WORKDAY.day][14] * workday_count

        s_kyori.append(str(ZeroCheck(Shin.MILEAGE)))

    ln_s_kyori = 0
    if s_kyori is not None:
        for s in s_kyori:
            ln_s_kyori += float(s)
        ln_s_kyori = math.floor(ln_s_kyori * 10) / 10

    # w_h = sum_0 // (60 * 60)
    # """ 24/8/1 修正分 """
    # w_m = (sum_0 - w_h * 60 * 60) / (60 * 60)
    # # 勤務時間合計
    # working_time = w_h + w_m
    # working_time_10 = sum_0 / (60 * 60)

    sum_over_0 = 0
    for n in range(len(over_time_0)):
        sum_over_0 += over_time_0[n]
    o_h = sum_over_0 // (60 * 60)
    """ 24/8/1 修正分 """
    o_m = (sum_over_0 - o_h * 60 * 60) / (60 * 60)
    over = o_h + o_m
    over_10 = sum_over_0 / (60 * 60)

    sum_hol_0 = 0
    for n in range(len(syukkin_holiday_times_0)):
        sum_hol_0 += syukkin_holiday_times_0[n]
    h_h = sum_hol_0 // (60 * 60)
    """ 24/8/1 修正分 """
    h_m = (sum_hol_0 - h_h * 60 * 60) / (60 * 60)
    holiday_work = h_h + h_m
    holiday_work_10 = sum_hol_0 / (60 * 60)

    # 配列に入った出勤時間(秒単位)を時間と分に変換
    """ 24/8/8 修正分 """
    syukkin_times = [
        # n // (60 * 60) + ((n - (n // (60 * 60)) * 60 * 60) // 60) / 100
        n // (60 * 60) + (n - (n // (60 * 60) * 3600)) / (60 * 60)
        for n in syukkin_times_0
    ]
    for n in range(len(syukkin_times)):
        AttendanceDada[Shin.WORKDAY.day][13] += syukkin_times[n]

    return render_template(
        "attendance/index.html",
        title="ホーム",
        cal=cal,
        shinseis=shinseis,
        y=y,
        m=m,
        form=form,
        form_month=form_month,
        oc=oc,
        oc_cnt=oc_cnt,
        eg=eg,
        sk=sk,
        othr=othr,
        hld=hld,
        u=u,
        bk=bk,
        tbl_clm=tbl_clm,
        typ=typ,
        ptn=ptn,
        specification=specification,
        wk=wk,
        td1=td1,
        td2=td2,
        td3=td3,
        td4=td4,
        td5=td5,
        td6=td6,
        td7=td7,
        td8=td8,
        td9=td9,
        td10=td10,
        td11=td11,
        td12=td12,
        td13=td13,
        td14=td14,
        td15=td15,
        td16=td16,
        workday_data=workday_data,
        cnt_attemdance=cnt_attemdance,
        reload_y=reload_y,
        td17=td17,
        td18=td18,
        td19=td19,
        td20=td20,
        stf_login=stf_login,
        length_oncall=length_oncall,
        team=team,
        jobtype=jobtype,
        team_name=team_name,
        length_oncall_1=length_oncall_1,
        length_oncall_2=length_oncall_2,
        length_oncall_3=length_oncall_3,
        length_oncall_4=length_oncall_4,
        length_oncall_5=length_oncall_5,
        length_oncall_6=length_oncall_6,
        length_oncall_7=length_oncall_7,
        length_oncall_8=length_oncall_8,
        dsp_page=dsp_page,
        STAFFID=STAFFID,
        template1=template1,
        template2=template2,
        AttendanceDada=AttendanceDada,
        working_time=work_time_sum,
        ln_s_kyori=ln_s_kyori,
        workday_count=workday_count,
        holiday_work=holiday_work,
        intFlg=intFlg,
    )
