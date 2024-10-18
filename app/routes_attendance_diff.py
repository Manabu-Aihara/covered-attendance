import os, math
from functools import wraps
from typing import Optional
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
    D_HOLIDAY_HISTORY,
    RecordPaidHoliday,
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
from app.attendance_query_class import AttendanceQuery
from app.new_calendar import NewCalendar

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


##### カレンダーとM_NOTIFICATION土日出勤の紐づけ関数 #####


def get_day_of_week_jp(form_date: datetime) -> str:
    w_list = ["", "", "", "", "", "1", "1"]
    return w_list[form_date.weekday()]


def get_move_distance(form_distance: str) -> Optional[str]:
    if form_distance is not None and form_distance != "":
        ZEN = "".join(chr(0xFF01 + j) for j in range(94))
        HAN = "".join(chr(0x21 + k) for k in range(94))
        ZEN2HAN = str.maketrans(ZEN, HAN)
        str_distance = form_distance.translate(ZEN2HAN)

        def is_num(s) -> float:
            try:
                float(s)
            except ValueError:
                return flash("数字以外は入力できません。")
            else:
                return s

        num_distance = is_num(str_distance)

        result_distance = str(
            Decimal(num_distance).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        )
        return result_distance
    else:
        result_distance = None
        return result_distance


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
    elif u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE > 2:
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
    notification_items = [db.session.get(Todokede, i) for i in range(1, 21)]
    # notification_items[15] = notification_items[9]
    exclude_list = [3, 5, 7, 8, 17, 18, 19, 20]
    notification_pm_list = [
        n for i, n in enumerate(notification_items, 1) if i not in exclude_list
    ]

    ##### 月選択の有無 #####
    # dsp_page = ""
    # 参照モードの場合、
    dsp_page = ""
    if intFlg == 3:
        # 参照モード
        dsp_page = "pointer-events: none;"

    # これは結構使い道あり！👍
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

    s_kyori = []  ################################################## 使用
    syukkin_times_0 = []  ################################################# 使用
    syukkin_holiday_times_0 = []  ################################################# 使用
    real_time = []
    real_time_sum = []
    over_time_0 = []

    team = u.TEAM_CODE  # この職員のチームコード
    jobtype = u.JOBTYPE_CODE  # この職員の職種

    # これも結構使い道あり！👍
    FromDay = date(y, m, 1)
    d = get_last_date(y, m)
    ToDay = date(y, m, d)

    shinseis = (
        db.session.query(Shinsei)
        .filter(
            and_(Shinsei.STAFFID == STAFFID, Shinsei.WORKDAY.between(FromDay, ToDay))
        )
        .all()
    )
    n = STAFFID  # ?

    # 出退勤テンプレートの取得(月途中で契約変更された場合の考慮)
    template1 = 0
    template2 = 0

    attendace_qry_obj = AttendanceQuery(STAFFID, FromDay, ToDay)
    templates = attendace_qry_obj.get_templates().group_by(
        M_TIMECARD_TEMPLATE.TEMPLATE_NO
    )

    # 月の途中の契約変更1回までは対応
    for template in templates:
        if template1 == 0:
            template1 = template.TEMPLATE_NO
        else:
            template2 = template.TEMPLATE_NO

    onc = []
    onc_1 = []
    onc_2 = []
    onc_3 = []
    onc_4 = []
    onc_5 = []
    onc_6 = []
    onc_7 = []
    onc_8 = []

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
                print(f"消滅します {row.WORKDAY}")

        reload_y = request.form.get("reload_h")
        ##### データ取得 #####
        # cal = []
        calendar_obj = NewCalendar(y, m)
        str_date_list = [
            f"{y}-{m}-{date_tuple[0]}"
            for date_tuple in calendar_obj.get_itermonthdays()
        ]
        i = 0
        for c in cal:
            # for str_date in str_date_list:
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
            data12 = request.form.get("alcohol" + str(i))  # アルコール

            ##### 勤怠条件分け #####
            # c = datetime.strptime(str_date, "%Y-%m-%d")[0]
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
            data4 = get_move_distance(data_4)

            todokede_AM = data7
            zangyou = 1 if data8 == "on" else 0
            todokede_PM = data11

            holiday = ""
            if jpholiday.is_holiday_name(datetime.strptime(data1, "%Y-%m-%d")):
                # 要は祝日
                holiday = "2"
            elif get_day_of_week_jp(datetime.strptime(data1, "%Y-%m-%d")) == "1":
                # 要は土日
                holiday = "1"

            oncall: int = 0
            oncall_cnt: str = "0"
            engel: str = "0"
            alc: int = 0
            # 登録するかの判定
            # 開始時間
            if (
                data2 != "00:00"
                or data3 != "00:00"
                or (data4 is not None and data4 != "0.0" and data4 != "")
                or blankCheck(data6) is not None
                or blankCheck(todokede_AM) is not None
                or blankCheck(todokede_PM) is not None
                or blankCheck(data9) is not None
                or data10 != ""
                or blankCheck(data12) is not None
            ):
                if data5 == "on":
                    oncall = 1
                    print(f"5: {oncall}")
                if data6 != "0":
                    oncall_cnt = data6
                if data9 != "0":
                    engel = data9
                    print(f"9: {engel}")
                if data12 == "on":
                    alc = 1
                    print(f"12: {alc}")

                InsertFlg = 1
            # else:
            #     print(f"Flag false!!: {c}")

            if InsertFlg == 1:
                print(f"消滅しません: {c}")
                AddATTENDANCE = Shinsei(
                    STAFFID,
                    data1,
                    holiday,
                    data2,
                    data3,
                    data4,
                    oncall,
                    oncall_cnt,
                    engel,
                    todokede_AM,
                    todokede_PM,
                    zangyou,
                    alc,
                    data10,
                )
                db.session.add(AddATTENDANCE)
            i = i + 1

        db.session.commit()

    """ ここから、押下後の表示 """
    # d = get_last_date(y, m)
    # 配列に初期値入れてデータの存在するとこに入れる
    # オンコールカウント用　2次元配列
    AttendanceDada = [["" for i in range(16)] for j in range(d + 1)]
    # AttendanceDada[日付][項目]

    calendar_obj = NewCalendar(y, m)
    str_date_list = [
        f"{y}-{m}-{date_tuple[0]}" for date_tuple in calendar_obj.get_itermonthdays()
    ]
    # 初期値
    i = 1
    for c in cal:
        # for str_date in str_date_list:
        #     c = datetime.strptime(str_date, "%Y-%m-%d")
        # print(f"cal 一個: {c}")
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

    # attendace_qry_obj = AttendanceQuery(STAFFID, FromDay, ToDay)
    attendance_query_list = attendace_qry_obj.get_attendance_query().order_by(
        Shinsei.STAFFID, Shinsei.WORKDAY
    )

    workday_count: int = 0
    work_time_sum: float = 0.0

    """ D_JOB_HISTORYに値がそろってないと、以下動きません """

    for attendace_query in attendance_query_list:
        Shin = attendace_query[0]
        print(f"{Shin.WORKDAY.day} 日")
        print(f"Notice PM: {Shin.NOTIFICATION2}")
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

        # あくまで暫定的に使う変数
        related_holiday = db.session.get(RecordPaidHoliday, Shin.STAFFID)
        settime = CalcTimeClass(
            dtm,
            Shin.NOTIFICATION,
            Shin.NOTIFICATION2,
            Shin.STARTTIME,
            Shin.ENDTIME,
            Shin.OVERTIME,
            attendace_query.CONTRACT_CODE,
            AttendanceDada,
            over_time_0,
            real_time,
            real_time_sum,
            syukkin_holiday_times_0,
            Shin.HOLIDAY,
            attendace_query.JOBTYPE_CODE,
            STAFFID,
            Shin.WORKDAY,
            # attendace_query.HOLIDAY_TIME,
            related_holiday.BASETIMES_PAIDHOLIDAY,
        )
        settime.calc_time()

        """ 24/8/1 変更分 """
        contract_work_time: float = 0.0
        if attendace_query.CONTRACT_CODE == 2:
            contract_work_time = attendace_query.PART_WORKTIME
        else:
            work_time = (
                db.session.query(KinmuTaisei.WORKTIME)
                .filter(KinmuTaisei.CONTRACT_CODE == attendace_query.CONTRACT_CODE)
                .first()
            )
            contract_work_time = work_time.WORKTIME

        print(f"aD 1 worktime: {AttendanceDada[Shin.WORKDAY.day][14]}")
        print(f"Real time: {real_time}")
        print(f"Real time list: {real_time_sum}")
        # print(f"What?: {syukkin_times_0}")
        # sum_0 += AttendanceDada[Shin.WORKDAY.day][14]

        w_h = AttendanceDada[Shin.WORKDAY.day][14] // (60 * 60)
        # """ 24/8/1 修正分 """
        w_m = (AttendanceDada[Shin.WORKDAY.day][14] - w_h * 60 * 60) / (60 * 60)
        """ 24/8/16 追加(勤務時間合計、残業考慮なしver) """
        # if (
        #     AttendanceDada[Shin.WORKDAY.day][7] != "00:00"
        #     and AttendanceDada[Shin.WORKDAY.day][8] != "00:00"
        # ):
        #     AttendanceDada[Shin.WORKDAY.day][14] = contract_work_time
        #     # if AttendanceData[Shin.WORKDAY.day][14] != 0:
        #     workday_count += 1
        #     work_time_sum = AttendanceDada[Shin.WORKDAY.day][14] * workday_count

        """ 24/9/20 変更 """
        # 出勤してたら
        if (
            AttendanceDada[Shin.WORKDAY.day][7] != "00:00"
            and AttendanceDada[Shin.WORKDAY.day][8] != "00:00"
        ):
            if (
                AttendanceDada[Shin.WORKDAY.day][10] == "1"
                or AttendanceDada[Shin.WORKDAY.day][10] == "2"
            ) or (
                AttendanceDada[Shin.WORKDAY.day][11] == "1"
                or AttendanceDada[Shin.WORKDAY.day][11] == "2"
            ):
                AttendanceDada[Shin.WORKDAY.day][14] = w_h + w_m
            else:
                if Shin.OVERTIME == "1":
                    AttendanceDada[Shin.WORKDAY.day][14] = w_h + w_m
                else:
                    AttendanceDada[Shin.WORKDAY.day][14] = contract_work_time

            workday_count += 1
            work_time_sum = AttendanceDada[Shin.WORKDAY.day][14] * workday_count
        # 1日有休 or 1日出張
        else:
            if (
                AttendanceDada[Shin.WORKDAY.day][10] == "3"
                or AttendanceDada[Shin.WORKDAY.day][10] == "5"
            ):
                AttendanceDada[Shin.WORKDAY.day][14] = contract_work_time
                work_time_sum = AttendanceDada[Shin.WORKDAY.day][14] * workday_count

        print(f"aD 2 worktime: {AttendanceDada[Shin.WORKDAY.day][14]}")

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

    print(f"Over time list: {over_time_0}")
    sum_over_0 = 0
    for n in range(len(over_time_0)):
        sum_over_0 += over_time_0[n]
    o_h = sum_over_0 // (60 * 60)
    o_m = (sum_over_0 - o_h * 60 * 60) // 60
    over = o_h + o_m / 100
    over_10 = sum_over_0 / (60 * 60)

    sum_hol_0 = 0
    for n in range(len(syukkin_holiday_times_0)):
        sum_hol_0 += syukkin_holiday_times_0[n]
    h_h = sum_hol_0 // (60 * 60)
    h_m = (sum_hol_0 - h_h * 60 * 60) // 60
    holiday_work = h_h + h_m / 100
    print(f"Holiday work: {holiday_work}")
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
        print(f"Work time list: {AttendanceDada[Shin.WORKDAY.day][13]}")

    return render_template(
        "attendance/index_diff_diff.html",
        title="ホーム",
        notifi_lst=notification_items,
        notifi_pm_lst=notification_pm_list,
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
        workday_data=workday_data,
        cnt_attemdance=cnt_attemdance,
        reload_y=reload_y,
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
